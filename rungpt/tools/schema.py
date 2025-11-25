"""Schema - 自动提取函数签名（增强版）"""
import inspect
from typing import Callable, Dict, Any, get_type_hints, get_origin, get_args


def extract_schema(func: Callable, pydantic_model: Any = None) -> Dict[str, Any]:
    """
    从函数签名或 Pydantic 模型自动提取参数 Schema
    
    Args:
        func: 函数对象
        pydantic_model: Pydantic BaseModel 类（可选）
        
    Returns:
        参数 Schema 字典
        
    Example:
        def search(query: str, limit: Optional[int] = 10) -> str:
            pass
        
        schema = extract_schema(search)
        # {
        #   "query": {"type": "string", "required": True},
        #   "limit": {"type": "integer", "required": False, "default": 10}
        # }
    """
    # 如果提供了 Pydantic 模型，优先使用
    if pydantic_model is not None:
        return _extract_from_pydantic(pydantic_model)
    
    schema = {}
    sig = inspect.signature(func)
    
    try:
        type_hints = get_type_hints(func)
    except:
        type_hints = {}
    
    for param_name, param in sig.parameters.items():
        param_schema = {}
        
        # 类型映射（增强版）
        if param_name in type_hints:
            py_type = type_hints[param_name]
            type_info = _map_type_enhanced(py_type)
            param_schema.update(type_info)
        
        # 是否必需
        param_schema["required"] = param.default == inspect.Parameter.empty
        
        # 默认值
        if param.default != inspect.Parameter.empty:
            param_schema["default"] = param.default
            # 如果有默认值，标记为非必需
            param_schema["required"] = False
        
        schema[param_name] = param_schema
    
    # 提取文档字符串
    if func.__doc__:
        schema["__doc__"] = func.__doc__.strip()
    
    return schema


def _extract_from_pydantic(model_class: Any) -> Dict[str, Any]:
    """从 Pydantic BaseModel 提取 Schema"""
    try:
        # 检查是否是 Pydantic v2
        if hasattr(model_class, 'model_fields'):
            # Pydantic v2
            schema = {}
            for field_name, field_info in model_class.model_fields.items():
                field_schema = {
                    "type": _map_type_enhanced(field_info.annotation).get("type", "string"),
                    "required": field_info.is_required(),
                }
                if field_info.default is not None:
                    field_schema["default"] = field_info.default
                if field_info.description:
                    field_schema["description"] = field_info.description
                schema[field_name] = field_schema
            return schema
        # Pydantic v1
        elif hasattr(model_class, '__fields__'):
            schema = {}
            for field_name, field_info in model_class.__fields__.items():
                field_schema = {
                    "type": _map_type_enhanced(field_info.outer_type_).get("type", "string"),
                    "required": field_info.required,
                }
                if field_info.default is not None:
                    field_schema["default"] = field_info.default
                if field_info.field_info.description:
                    field_schema["description"] = field_info.field_info.description
                schema[field_name] = field_schema
            return schema
    except Exception:
        pass
    
    return {}


def _map_type_enhanced(py_type) -> Dict[str, Any]:
    """
    增强版类型映射，支持 Optional、Union、List[T] 等复杂类型
    
    Returns:
        包含 type 和其他元信息的字典
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object"
    }
    
    # 处理基础类型
    if py_type in type_map:
        return {"type": type_map[py_type]}
    
    # 获取泛型的 origin 和 args
    origin = get_origin(py_type)
    args = get_args(py_type)
    
    # 处理 Optional[T] (等价于 Union[T, None])
    if origin is type(None) or (origin is type(None).__class__):
        return {"type": "null"}
    
    # 处理 Union 类型
    if origin is type(int | str):  # Python 3.10+ 的 Union 语法
        origin = type(int).__class__.__bases__[0]  # 获取 Union
    
    # 兼容不同 Python 版本的 Union 检查
    import typing
    if hasattr(typing, 'Union') and origin is typing.Union:
        # 过滤掉 None，获取实际类型
        non_none_types = [t for t in args if t is not type(None)]
        if len(non_none_types) == 1:
            # Optional[T] 的情况
            return _map_type_enhanced(non_none_types[0])
        elif len(non_none_types) > 1:
            # Union[T1, T2, ...] 的情况，返回第一个类型
            return _map_type_enhanced(non_none_types[0])
    
    # 处理 List[T]
    if origin is list:
        result = {"type": "array"}
        if args:
            item_type = _map_type_enhanced(args[0])
            result["items"] = item_type
        return result
    
    # 处理 Dict[K, V]
    if origin is dict:
        return {"type": "object"}
    
    # 处理其他泛型
    if origin:
        return {"type": type_map.get(origin, "string")}
    
    # 默认返回 string
    return {"type": "string"}


def _map_type(py_type) -> str:
    """向后兼容的简单类型映射"""
    result = _map_type_enhanced(py_type)
    return result.get("type", "string")

