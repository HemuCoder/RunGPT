"""
Workflow Core Abstractions
定义 Step, Context 和 Pipeline 核心类。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

class WorkflowContext(dict):
    """
    工作流上下文
    
    用于在 Step 之间传递数据。
    支持属性访问 (context.key) 和字典访问 (context['key'])。
    """
    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'WorkflowContext' object has no attribute '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def merge(self, other: Dict[str, Any]) -> None:
        """合并其他字典到上下文"""
        self.update(other)


class Step(ABC):
    """
    工作流步骤基类 (Abstract Base Class)
    
    所有工作流节点（Agent, Tool, Logic）都必须继承此类。
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, context: WorkflowContext) -> Any:
        """
        执行步骤
        
        Args:
            context: 工作流上下文
            
        Returns:
            执行结果
        """
        pass

    def __call__(self, context: WorkflowContext) -> Any:
        """允许像函数一样调用 Step"""
        return self.run(context)


class Pipeline(Step):
    """
    线性工作流 (Pipeline)
    
    按顺序执行一组 Step。前一个 Step 的输出可以作为后一个 Step 的输入（通过 Context 传递）。
    """
    def __init__(self, steps: List[Step], name: str = "Pipeline"):
        super().__init__(name)
        self.steps = steps

    def run(self, context: Union[WorkflowContext, Dict[str, Any]]) -> Any:
        """
        执行 Pipeline
        
        Args:
            context: 初始上下文 (可以是 dict)
            
        Returns:
            最后一个 Step 的执行结果
        """
        # 确保 context 是 WorkflowContext 对象
        if not isinstance(context, WorkflowContext):
            context = WorkflowContext(context)
        
        logger.info(f"[{self.name}] Started with context keys: {list(context.keys())}")
        
        last_result = None
        for step in self.steps:
            logger.info(f"[{self.name}] Running step: {step.name}")
            try:
                last_result = step.run(context)
            except Exception as e:
                logger.error(f"[{self.name}] Step '{step.name}' failed: {str(e)}")
                raise e
                
        logger.info(f"[{self.name}] Finished")
        return last_result
