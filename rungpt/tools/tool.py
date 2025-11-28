"""Tool - 工具定义（增强版）"""
import inspect
from typing import Callable, Dict, Any, Optional, Type
from dataclasses import dataclass
from pydantic import BaseModel, create_model
from .result import ToolResult


def _create_dynamic_model(func: Callable) -> Optional[Type[BaseModel]]:
    """
    从函数签名动态构建 Pydantic 模型。
    这是一个辅助函数，用于将函数签名转换为 Pydantic 模型定义。
    """
    sig = inspect.signature(func)
    fields = {}

    for param_name, param in sig.parameters.items():
        # 跳过 self/cls
        if param_name in ('self', 'cls'):
            continue

        # 获取类型注解
        annotation = param.annotation
        if annotation == inspect.Parameter.empty:
            annotation = Any

        # 获取默认值
        default = param.default
        if default == inspect.Parameter.empty:
            # 必需参数: (Type, ...)
            fields[param_name] = (annotation, ...)
        else:
            # 可选参数: (Type, default)
            fields[param_name] = (annotation, default)

    try:
        # 动态创建 Pydantic 模型
        DynamicModel = create_model(f"{func.__name__}Args", **fields)
        return DynamicModel
    except Exception as e:
        # 让错误在工具注册时就暴露,而不是运行时静默失败
        raise ValueError(
            f"无法为函数 '{func.__name__}' 创建 Pydantic 验证模型。"
            f"请确保所有参数都有明确的类型注解。原因: {e}"
        ) from e


def _extract_from_pydantic_model(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """从 Pydantic 模型提取符合 OpenAI Function Calling 格式的 Schema"""
    try:
        # 获取 JSON Schema
        json_schema = model_class.model_json_schema()
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])
        
        # 转换为我们需要的格式
        schema = {}
        for name, prop in properties.items():
            param_schema = {
                "type": prop.get("type", "string"),
                "description": prop.get("description", ""),
                "required": name in required
            }
            
            # 处理复杂类型 (array, object, enum 等)
            if "items" in prop:
                param_schema["items"] = prop["items"]
            if "enum" in prop:
                param_schema["enum"] = prop["enum"]
            if "properties" in prop:
                param_schema["properties"] = prop["properties"]
            if "anyOf" in prop:
                # 处理 Optional 或 Union 类型
                types = [t.get("type") for t in prop["anyOf"] if t.get("type") != "null"]
                if types:
                    # 主类型取第一个(兼容性考虑)
                    param_schema["type"] = types[0]
                    # 如果有多个类型,在描述中说明
                    if len(types) > 1:
                        type_desc = f"可接受类型: {', '.join(types)}"
                        if param_schema.get("description"):
                            param_schema["description"] += f" ({type_desc})"
                        else:
                            param_schema["description"] = type_desc
            
            # 处理默认值
            if "default" in prop:
                param_schema["default"] = prop["default"]
                param_schema["required"] = False
            
            # 清理空描述
            if not param_schema["description"]:
                param_schema.pop("description")
                
            schema[name] = param_schema
            
        return schema
    except Exception as e:
        raise ValueError(
            f"无法从 Pydantic 模型 '{model_class.__name__}' 提取 Schema。"
            f"请检查模型定义是否正确。原因: {e}"
        ) from e


def extract_function_schema(
    func: Callable, pydantic_model: Optional[Type[BaseModel]] = None
) -> Dict[str, Any]:
    """
    从函数签名或 Pydantic 模型自动提取参数 Schema

    Args:
        func: 函数对象
        pydantic_model: Pydantic BaseModel 类（可选）

    Returns:
        参数 Schema 字典
    """
    # 1. 如果提供了 Pydantic 模型，直接使用
    if pydantic_model is not None:
        return _extract_from_pydantic_model(pydantic_model)

    # 2. 从函数签名动态构建 Pydantic 模型
    DynamicModel = _create_dynamic_model(func)
    if DynamicModel is None:
        return {}

    return _extract_from_pydantic_model(DynamicModel)


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
    _validation_model: Optional[Any] = None  # 内部使用的验证模型
    
    def __post_init__(self):
        # 如果提供了 Pydantic 模型，优先使用
        if self.args_schema is not None:
            self.parameters = extract_function_schema(self.func, pydantic_model=self.args_schema)
            self._validation_model = self.args_schema
        elif self.parameters is None:
            # 从函数签名动态创建 Pydantic 模型
            self._validation_model = _create_dynamic_model(self.func)
            self.parameters = extract_function_schema(self.func)
        
        if not self.description and self.func.__doc__:
            self.description = self.func.__doc__.strip().split('\n')[0]
    
    def call(self, **kwargs) -> ToolResult:
        """
        调用工具
        
        如果设置了 args_schema (Pydantic 模型),会先进行参数验证和类型转换
        
        Returns:
            ToolResult 对象
        """
        # 使用验证模型进行参数验证和类型转换
        if self._validation_model is not None:
            try:
                # 使用 Pydantic 验证和转换参数
                validated_args = self._validation_model(**kwargs)
                # 转换为字典传递给函数,mode='python' 确保类型强制转换
                # 例如: "123" → 123, "true" → True
                if hasattr(validated_args, 'model_dump'):
                    # Pydantic v2
                    kwargs = validated_args.model_dump(mode='python')
                else:
                    # Pydantic v1 兼容
                    kwargs = validated_args.dict()
            except Exception as e:
                # 验证失败,返回错误
                return ToolResult.fail(f"参数验证失败: {str(e)}")
        
        # 调用函数
        try:
            result = self.func(**kwargs)
            
            # 强制要求返回 ToolResult
            if not isinstance(result, ToolResult):
                raise TypeError(
                    f"工具 '{self.name}' 必须返回 ToolResult 对象,但返回了 {type(result).__name__}。"
                    f"请使用 ToolResult.ok(data) 或 ToolResult.fail(error) 包装返回值。"
                )
            
            return result
        except Exception as e:
            # 捕获执行错误
            return ToolResult.fail(f"工具执行失败: {str(e)}")
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的完整 Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

