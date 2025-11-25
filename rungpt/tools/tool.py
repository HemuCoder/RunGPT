"""Tool - 工具定义（增强版）"""
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
from .schema import extract_schema
from .result import ToolResult


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
        args_schema: Pydantic BaseModel 类（可选，用于参数验证）
    """
    name: str
    func: Callable
    description: str = ""
    parameters: Optional[Dict[str, Any]] = None
    enabled: bool = True
    args_schema: Optional[Any] = None  # Pydantic BaseModel 类
    
    def __post_init__(self):
        # 如果提供了 Pydantic 模型，优先使用
        if self.args_schema is not None:
            self.parameters = extract_schema(self.func, pydantic_model=self.args_schema)
        elif self.parameters is None:
            self.parameters = extract_schema(self.func)
        
        if not self.description and self.func.__doc__:
            self.description = self.func.__doc__.strip().split('\n')[0]
    
    def call(self, **kwargs) -> Any:
        """
        调用工具
        
        如果设置了 args_schema (Pydantic 模型)，会先进行参数验证和类型转换
        """
        # 如果有 Pydantic 模型，先验证参数
        if self.args_schema is not None:
            try:
                # 使用 Pydantic 验证和转换参数
                validated_args = self.args_schema(**kwargs)
                # 转换为字典传递给函数
                kwargs = validated_args.dict() if hasattr(validated_args, 'dict') else validated_args.model_dump()
            except Exception as e:
                # 验证失败，返回错误
                return ToolResult.fail(f"参数验证失败: {str(e)}")
        
        # 调用函数
        result = self.func(**kwargs)
        
        # 如果返回的不是 ToolResult，自动包装
        if not isinstance(result, ToolResult):
            # 如果是字典且包含 success 字段，尝试转换
            if isinstance(result, dict) and "success" in result:
                if result["success"]:
                    return ToolResult.ok(result.get("data"))
                else:
                    return ToolResult.fail(result.get("error", "Unknown error"))
            # 否则视为成功结果
            return ToolResult.ok(result)
        
        return result
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的完整 Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

