"""Tool - 工具定义"""
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass, field
from .schema import extract_schema


@dataclass
class Tool:
    """
    工具定义
    
    Attributes:
        name: 工具名称
        func: 工具函数
        description: 工具描述
        parameters: 参数 Schema（自动提取或手动指定）
        enabled: 是否启用
    """
    name: str
    func: Callable
    description: str = ""
    parameters: Optional[Dict[str, Any]] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = extract_schema(self.func)
        
        if not self.description and self.func.__doc__:
            self.description = self.func.__doc__.strip().split('\n')[0]
    
    def call(self, **kwargs) -> Any:
        """调用工具"""
        return self.func(**kwargs)
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的完整 Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

