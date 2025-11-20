"""ReAct Agent - 支持工具调用的 Agent"""
from typing import Optional, Dict, Any, List
from .agent_base import AgentBase
from .react_parser import ReActParser, Action
from ..threads import Thread
from ..tools import ToolRegistry


class ReActStep:
    """ReAct 循环的单步记录"""
    
    def __init__(self, step_num: int):
        self.step_num = step_num
        self.thought: Optional[str] = None
        self.action: Optional[Action] = None
        self.observation: Optional[str] = None
        self.raw_response: str = ""
        self.is_final: bool = False
        self.final_answer: Optional[str] = None


class ReActAgent(AgentBase):
    """ReAct Agent - 支持推理和行动循环"""
    
    def __init__(
        self,
        system_prompt: str,
        model: str,
        tools: Optional[ToolRegistry] = None,
        **kwargs
    ):
        """
        初始化 ReAct Agent
        
        Args:
            system_prompt: 系统提示词
            model: 模型名称（如 "gpt-4o"）
            tools: 工具注册表（可选，默认创建空的）
            **kwargs: 其他参数（name, temperature, max_steps, memory, stream, verbose, debug等）
        """
        super().__init__(system_prompt, model, **kwargs)
        self.tools = tools or ToolRegistry()
        self.parser = ReActParser()
        self.react_steps: List[ReActStep] = []
        
        if self.stream and self.verbose:
            print("💬 ReActAgent 启用流式输出模式\n")
    
    def _execute(self, task: str, thread: Thread) -> str:
        """
        执行 ReAct 循环
        
        Args:
            task: 任务描述
            thread: 对话线程
            
        Returns:
            最终答案
        """
        thread.add_user(task)
        self.react_steps = []
        
        for step_num in range(1, self.profile.max_steps + 1):
            current_step = ReActStep(step_num)
            
            if self.verbose:
                print(f"\n{'='*70}")
                print(f"🔄 Step {step_num}")
                print(f"{'='*70}")
            
            # 调用模型
            response = self._call_model(thread)
            current_step.raw_response = response
            
            # 先解析 Thought 和 Action
            thought = self.parser.extract_thought(response)
            action = self.parser.parse(response)
            
            if self.verbose and thought:
                print(f"💭 Thought: {thought}")
            
            # 如果有 Action，执行工具调用或结束
            if action:
                current_step.thought = thought
                current_step.action = action
                
                # 检查是否是 Finish action
                if action.name == "FINISH":
                    final_answer = action.params.get("answer", "")
                    current_step.is_final = True
                    current_step.final_answer = final_answer
                    self.react_steps.append(current_step)
                    
                    if self.verbose:
                        print(f"⚡ Action: Finish[{final_answer[:50]}...]")
                        print(f"\n{'='*70}")
                        print(f"✅ Final Answer: {final_answer}")
                        print(f"{'='*70}\n")
                    
                    thread.add_assistant(response)
                    return final_answer
                
                # 普通工具调用
                if self.verbose:
                    print(f"⚡ Action: {action.name}[{action.params}]")
                
                # 执行工具
                observation = self.tools.call(action.name, action.params)
                current_step.observation = observation
                self.react_steps.append(current_step)
                
                if self.verbose:
                    print(f"👁️  Observation: {observation}")
                
                # 将结果添加到对话
                thread.add_assistant(response)
                thread.add_user(f"Observation: {observation}")
                continue
            
            # 没有 Action，检查是否是 Final Answer
            if self.parser.has_finish(response):
                final_answer = self._extract_final_answer(response)
                current_step.is_final = True
                current_step.final_answer = final_answer
                current_step.thought = thought
                self.react_steps.append(current_step)
                
                if self.verbose:
                    print(f"\n{'='*70}")
                    print(f"✅ Final Answer: {final_answer}")
                    print(f"{'='*70}\n")
                
                thread.add_assistant(response)
                return final_answer
            
            # 既没有 Action 也没有 Final Answer
            if self.verbose:
                print(f"⚠️  模型输出格式错误，未检测到 Action 或 Final Answer")
                
                current_step.is_final = True
                current_step.final_answer = response
            self.react_steps.append(current_step)
            thread.add_assistant(response)
            return response
        
        # 达到最大步数
        if self.verbose:
            print(f"\n⚠️  达到最大步数限制 ({self.profile.max_steps})")
        
        return "达到最大步数限制"
    
    def _extract_final_answer(self, response: str) -> str:
        """
        从响应中提取最终答案
        
        Args:
            response: 模型响应
            
        Returns:
            最终答案文本
        """
        import re
        
        patterns = [
            r'Final Answer:\s*(.*?)(?:\n|$)',
            r'最终答案：\s*(.*?)(?:\n|$)',
            r'Answer:\s*(.*?)(?:\n|$)',
            r'答案：\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # 如果没有匹配到，返回整个响应
        return response.strip()
    
    def get_react_steps(self) -> List[Dict[str, Any]]:
        """
        获取 ReAct 步骤记录
        
        Returns:
            步骤记录列表
        """
        return [
            {
                "step_num": step.step_num,
                "thought": step.thought,
                "action": {
                    "name": step.action.name,
                    "params": step.action.params
                } if step.action else None,
                "observation": step.observation,
                "is_final": step.is_final,
                "final_answer": step.final_answer
            }
            for step in self.react_steps
        ]
