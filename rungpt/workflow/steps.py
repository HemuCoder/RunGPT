"""
Standard Workflow Steps
提供常用的 Step 实现,包括 AgentStep (包装 Agent) 和 FunctionStep (包装函数)。
"""
from typing import Any, Callable, Optional, Dict, Union
from .core import Step, WorkflowContext
from ..agent.agent_base import AgentBase
from ..threads import Thread

class AgentStep(Step):
    """
    Agent 步骤
    
    将现有的 Agent (SimpleAgent, ReActAgent, PlanExecuteAgent) 包装为工作流步骤。
    """
    def __init__(
        self, 
        agent: AgentBase, 
        name: str,
        input_key: str = "task",
        output_key: str = "result",
        input_template: Optional[str] = None
    ):
        """
        初始化 AgentStep
        
        Args:
            agent: RunGPT Agent 实例
            name: 步骤名称
            input_key: 从 Context 中读取输入的键名 (默认 "task")
            output_key: 将结果写入 Context 的键名 (默认 "result")
            input_template: 输入模板 (例如 "请分析: {query}"),如果提供则忽略 input_key 直接使用模板渲染
        """
        super().__init__(name)
        self.agent = agent
        self.input_key = input_key
        self.output_key = output_key
        self.input_template = input_template

    def run(self, context: WorkflowContext) -> Any:
        # 1. 准备输入
        if self.input_template:
            # 使用模板渲染输入
            try:
                task_input = self.input_template.format(**context)
            except KeyError as e:
                raise ValueError(f"AgentStep '{self.name}' template missing key: {e}")
        else:
            # 直接从 Context 获取
            task_input = context.get(self.input_key)
            if task_input is None:
                raise ValueError(f"AgentStep '{self.name}' missing input key: '{self.input_key}'")

        # 2. 准备 Thread (每个 Step 使用独立的 Thread,或者从 Context 获取共享 Thread)
        # 目前策略: 每次创建新 Thread 以保持无状态,除非 Context 中显式传递了 thread
        thread = context.get("thread", Thread())

        # 3. 执行 Agent
        result = self.agent.run(task_input, thread)

        # 4. 写入输出
        context[self.output_key] = result
        
        return result


class FunctionStep(Step):
    """
    函数步骤
    
    将普通 Python 函数包装为工作流步骤。
    """
    def __init__(
        self, 
        func: Callable[[WorkflowContext], Any], 
        name: str = None
    ):
        """
        初始化 FunctionStep
        
        Args:
            func: 可调用对象,接收 WorkflowContext,返回任意值
            name: 步骤名称 (默认使用函数名)
        """
        super().__init__(name or func.__name__)
        self.func = func

    def run(self, context: WorkflowContext) -> Any:
        return self.func(context)
