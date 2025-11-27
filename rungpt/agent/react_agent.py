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
            result = self._execute_step(step_num, thread)
            if result:  # 如果返回结果,说明任务完成
                return result
        
        # 达到最大步数,强制结束
        return self._force_finish(thread)
    
    def _execute_step(self, step_num: int, thread: Thread) -> Optional[str]:
        """执行单个 ReAct 步骤"""
        current_step = ReActStep(step_num)
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"🔄 Step {step_num}")
            print(f"{'='*70}")
        
        # 调用模型
        response = self._call_model(thread)
        current_step.raw_response = response
        
        # 解析 Thought 和 Action
        thought = self.parser.extract_thought(response)
        action = self.parser.parse(response)
        
        if self.verbose and thought:
            print(f"💭 Thought: {thought}")
        
        # 处理不同情况
        if action:
            return self._handle_action(action, thought, response, current_step, thread)
        elif self.parser.has_finish(response):
            return self._handle_finish(response, thought, current_step, thread)
        else:
            self._handle_error(response, thought, current_step, thread)
            return None
    
    def _handle_action(self, action: Action, thought: Optional[str], 
                       response: str, step: ReActStep, thread: Thread) -> Optional[str]:
        """处理 Action:工具调用或完成"""
        step.thought = thought
        step.action = action
        
        # FINISH action
        if action.name == "FINISH":
            final_answer = action.params.get("answer", "")
            step.is_final = True
            step.final_answer = final_answer
            self.react_steps.append(step)
            
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
        
        observation = self.tools.call(action.name, action.params)
        step.observation = observation
        self.react_steps.append(step)
        
        if self.verbose:
            print(f"👁️  Observation: {observation}")
        
        thread.add_assistant(response)
        thread.add_user(f"Observation: {observation}")
        return None
    
    def _handle_finish(self, response: str, thought: Optional[str], 
                       step: ReActStep, thread: Thread) -> str:
        """处理 Final Answer(无 Action 格式)"""
        final_answer = self._extract_final_answer(response)
        step.is_final = True
        step.final_answer = final_answer
        step.thought = thought
        self.react_steps.append(step)
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"✅ Final Answer: {final_answer}")
            print(f"{'='*70}\n")
        
        thread.add_assistant(response)
        return final_answer
    
    def _handle_error(self, response: str, thought: Optional[str], 
                      step: ReActStep, thread: Thread) -> None:
        """处理格式错误:插入引导消息"""
        if self.verbose:
            print(f"⚠️  模型输出格式错误,未检测到 Action 或 Final Answer")
            print(f"📝 插入引导消息,要求模型重新输出正确格式")
        
        step.thought = thought
        self.react_steps.append(step)
        
        thread.add_assistant(response)
        
        guidance_message = (
            "你的输出格式不正确。请严格按照以下格式输出:\n\n"
            "如果需要使用工具:\n"
            "Thought: [你的思考过程]\n"
            "Action: tool_name[{\"param\": \"value\"}]\n\n"
            "如果已经得到最终答案:\n"
            "Thought: [你的思考过程]\n"
            "Action: FINISH[{\"answer\": \"你的最终答案\"}]\n\n"
            "请重新输出。"
        )
        thread.add_user(guidance_message)
    
    def _force_finish(self, thread: Thread) -> str:
        """强制结束:达到最大步数"""
        if self.verbose:
            print(f"\n⚠️  达到最大步数限制 ({self.profile.max_steps})")
            print(f"📝 插入强制消息,要求agent总结并输出最终答案")
        
        force_message = (
            "你已经达到最大步数限制。请立即基于目前已有的所有信息和观察结果,总结并输出最终答案。\n\n"
            "必须使用以下格式:\n"
            "Thought: [总结你的分析过程和已获得的信息]\n"
            "Action: FINISH[{\"answer\": \"你的最终答案\"}]\n\n"
            "即使信息不完整,也请给出你目前能够得出的最佳答案。"
        )
        thread.add_user(force_message)
        
        final_response = self._call_model(thread)
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"🔄 强制总结步骤")
            print(f"{'='*70}")
        
        # 尝试解析
        action = self.parser.parse(final_response)
        if action and action.name == "FINISH":
            final_answer = action.params.get("answer", "")
            if self.verbose:
                print(f"✅ Final Answer: {final_answer}")
                print(f"{'='*70}\n")
            thread.add_assistant(final_response)
            return final_answer
        
        if self.parser.has_finish(final_response):
            final_answer = self._extract_final_answer(final_response)
            if self.verbose:
                print(f"✅ Final Answer: {final_answer}")
                print(f"{'='*70}\n")
            thread.add_assistant(final_response)
            return final_answer
        
        # 兜底:返回原始响应
        if self.verbose:
            print(f"⚠️  模型仍未按格式输出,返回原始响应")
            print(f"{'='*70}\n")
        
        thread.add_assistant(final_response)
        return final_response
    
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
