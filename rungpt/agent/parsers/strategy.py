"""Parser Strategy - 解析器策略抽象基类"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Action:
    """执行动作"""
    name: str
    params: Dict[str, Any]
    raw: str = ""
    
    def __repr__(self) -> str:
        return f"Action(name={self.name}, params={self.params})"


class ParserStrategy(ABC):
    """
    解析器策略抽象基类
    
    每个具体策略负责解析一种特定格式的 Action
    """
    
    @abstractmethod
    def parse(self, text: str) -> Optional[Action]:
        """
        解析文本,提取 Action
        
        Args:
            text: 模型输出文本
            
        Returns:
            Action 对象或 None(如果无法解析)
        """
        pass
    
    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """
        快速判断是否可能处理此文本
        
        用于优化:避免尝试不可能成功的解析
        
        Args:
            text: 模型输出文本
            
        Returns:
            True 如果可能解析成功
        """
        pass
