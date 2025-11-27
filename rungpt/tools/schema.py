"""Schema - 自动提取函数签名（Pydantic 增强版）"""
import inspect
from typing import Callable, Dict, Any, Optional, Type
from pydantic import BaseModel, TypeAdapter, create_model
from pydantic.fields import FieldInfo


def extract_schema(func: Callable, pydantic_model: Optional[Type[BaseModel]] = None) -> Dict[str, Any]:
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
        return _extract_from_pydantic_model(DynamicModel)
    except Exception as e:
        # 兜底：如果动态创建失败（极少情况），返回空 Schema 或记录错误
        # 这里简单返回空，实际生产中可能需要 fallback 到旧逻辑
        return {}


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
                # 处理 Optional 或 Union
                # 简化处理：取第一个非 null 类型
                types = [t.get("type") for t in prop["anyOf"] if t.get("type") != "null"]
                if types:
                    param_schema["type"] = types[0]
            
            # 处理默认值
            if "default" in prop:
                param_schema["default"] = prop["default"]
                param_schema["required"] = False
            
            # 清理空描述
            if not param_schema["description"]:
                param_schema.pop("description")
                
            schema[name] = param_schema
            
        return schema
    except Exception:
        return {}
