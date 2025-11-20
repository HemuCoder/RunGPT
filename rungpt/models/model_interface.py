"""Model Interface - 定义统一的模型调用接口"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ModelInterface(ABC):
    """所有模型提供者的抽象基类"""
    
    def __init__(self, model_name: str, **config):
        self.model_name = model_name
        self.config = config
    
    @abstractmethod
    def run(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        执行模型推理
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数（如 temperature, max_tokens 等）
            
        Returns:
            str: 模型返回的文本内容
        """
        pass
    
    @abstractmethod
    def stream_run(self, messages: List[Dict[str, str]], **kwargs):
        """
        流式执行模型推理
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式返回的文本片段
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "provider": self.__class__.__name__,
            "config": self.config
        }

