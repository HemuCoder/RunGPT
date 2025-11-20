"""Simple Agent - 简单文本生成 Agent"""
from typing import Optional
from .agent_base import AgentBase
from .react_parser import ReActParser
from ..threads import Thread
from ..tools import ToolRegistry


class SimpleAgent(AgentBase):
    """简单 Agent，直接生成文本输出，支持可选工具调用"""
    
    def __init__(
        self, 
        system_prompt: str,
        model: str,
        tools: Optional[ToolRegistry] = None,
        **kwargs
    ):
        """
        初始化 Simple Agent
        
        Args:
            system_prompt: 系统提示词
            model: 模型名称（如 "gpt-4o"）
            tools: 工具注册表（可选）
            **kwargs: 其他参数（name, temperature, max_steps, memory, stream, verbose, debug等）
        """
        super().__init__(system_prompt, model, **kwargs)
        self.tools = tools
        self.parser = ReActParser() if tools else None
        
        if self.verbose:
            print(f"🤖 SimpleAgent 初始化")
            if self.tools:
                print(f"   可用工具: {', '.join(self.tools.list_tools())}")
            if self.stream:
                print(f"   流式输出: 已启用")
            print()
    
    def _execute(self, task: str, thread: Thread) -> str:
        """
        执行简单任务
        
        Args:
            task: 任务描述
            thread: 对话线程
            
        Returns:
            生成的文本
        """
        if self.verbose:
            print(f"{'='*70}")
            print(f"🎯 SimpleAgent 执行任务")
            print(f"{'='*70}")
            print(f"📝 任务: {task}")
            print(f"{'─'*70}\n")
        
        thread.add_user(task)
        
        # 调用模型
        if self.verbose:
            print("⏳ 调用模型...")
        
        response = self._call_model(thread)
        
        if self.verbose:
            print(f"💬 模型回复: {response}\n")
            print(f"{'─'*70}")
        
        # 如果配置了工具，检测是否需要工具调用
        if self.tools and self.parser:
            action = self.parser.parse(response)
            if action:
                if self.verbose:
                    print(f"🔧 检测到工具调用")
                    print(f"   工具: {action.name}")
                    print(f"   参数: {action.params}")
                    print(f"   执行中...")
                
                # 执行工具
                tool_result = self.tools.call(action.name, action.params)
                
                if self.verbose:
                    if "Error" in tool_result:
                        print(f"   ❌ 执行失败")
                    else:
                        print(f"   ✅ 执行成功")
                    print(f"   返回: {tool_result}")
                    print(f"{'─'*70}\n")
                
                # 将工具结果加入对话，让模型生成最终答案
                thread.add_assistant(response)
                thread.add_user(f"工具 {action.name} 返回结果：{tool_result}\n\n请基于此结果给出最终回答。")
                
                if self.verbose:
                    print("⏳ 调用模型生成最终答案...")
                
                final_response = self._call_model(thread)
                
                if self.verbose:
                    print(f"💬 最终答案: {final_response}\n")
                    print(f"{'='*70}\n")
                
                thread.add_assistant(final_response)
                return final_response
            else:
                if self.verbose:
                    print(f"ℹ️  未检测到工具调用，直接返回回答")
                    print(f"{'='*70}\n")
        
        # 如果没有工具或没有检测到工具调用
        thread.add_assistant(response)
        
        if self.verbose and not self.tools:
            print(f"{'='*70}\n")
        
        return response
