"""Model Registry - 模型注册表与加载管理"""
from typing import Dict, Type, Optional, Any
from .model_interface import ModelInterface
from .unified_provider import UnifiedProvider


class ModelRegistry:
    """模型注册表，管理所有可用的 Provider"""
    
    _providers: Dict[str, Type[ModelInterface]] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: Type[ModelInterface]):
        """
        注册一个新的 Provider
        
        Args:
            name: Provider 名称
            provider_class: Provider 类
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def get_provider(cls, name: str) -> Type[ModelInterface]:
        """
        获取已注册的 Provider
        
        Args:
            name: Provider 名称
            
        Returns:
            Provider 类
        """
        if name not in cls._providers:
            raise ValueError(f"Provider '{name}' 未注册，可用的有: {list(cls._providers.keys())}")
        return cls._providers[name]
    
    @classmethod
    def list_providers(cls) -> list:
        """列出所有已注册的 Provider"""
        return list(cls._providers.keys())


# 注册默认的 UnifiedProvider
ModelRegistry.register("unified", UnifiedProvider)


def load_model(
    provider: str = "unified",
    model_name: str = "deepseek-r1",
    **config
) -> ModelInterface:
    """
    加载模型实例
    
    Args:
        provider: Provider 名称，默认 "unified"
        model_name: 模型名称
        **config: 模型配置参数
        
    Returns:
        ModelInterface: 模型实例
        
    Example:
        model = load_model("unified", model_name="deepseek-r1")
        response = model.run([{"role": "user", "content": "Hello"}])
    """
    provider_class = ModelRegistry.get_provider(provider)
    return provider_class(model_name=model_name, **config)

