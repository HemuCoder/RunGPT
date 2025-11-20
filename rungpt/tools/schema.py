"""Schema - 自动提取函数签名"""
import inspect
from typing import Callable, Dict, Any, get_type_hints


def extract_schema(func: Callable) -> Dict[str, Any]:
    """
    从函数签名自动提取参数 Schema
    
    Args:
        func: 函数对象
        
    Returns:
        参数 Schema 字典
        
    Example:
        def search(query: str, limit: int = 10) -> str:
            pass
        
        schema = extract_schema(search)
        # {
        #   "query": {"type": "string", "required": True},
        #   "limit": {"type": "integer", "required": False, "default": 10}
        # }
    """
    schema = {}
    sig = inspect.signature(func)
    
    try:
        type_hints = get_type_hints(func)
    except:
        type_hints = {}
    
    for param_name, param in sig.parameters.items():
        param_schema = {}
        
        # 类型映射
        if param_name in type_hints:
            py_type = type_hints[param_name]
            param_schema["type"] = _map_type(py_type)
        
        # 是否必需
        param_schema["required"] = param.default == inspect.Parameter.empty
        
        # 默认值
        if param.default != inspect.Parameter.empty:
            param_schema["default"] = param.default
        
        schema[param_name] = param_schema
    
    # 提取文档字符串
    if func.__doc__:
        schema["__doc__"] = func.__doc__.strip()
    
    return schema


def _map_type(py_type) -> str:
    """Python 类型映射到 JSON Schema 类型"""
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object"
    }
    
    # 处理泛型类型
    origin = getattr(py_type, "__origin__", None)
    if origin:
        return type_map.get(origin, "string")
    
    return type_map.get(py_type, "string")

