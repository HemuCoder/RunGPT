"""Registry - 工具注册表"""
from typing import Dict, Callable, List, Optional, Any
from .tool import Tool
from .validators import ToolValidator, ValidationError


class ToolRegistry:
    """
    工具注册表
    
    支持三种注册方式：
    1. 简单注册: registry.register("name", func)
    2. 装饰器注册: @registry.tool()
    3. 完整注册: registry.register_tool(Tool(...))
    """
    
    def __init__(self, enable_validation: bool = False):
        self._tools: Dict[str, Tool] = {}
        self.validator = ToolValidator() if enable_validation else None
    
    def register(self, name: str, func: Callable, description: str = "", 
                 schema: Optional[Dict[str, Any]] = None) -> None:
        """
        简单注册（向后兼容）
        
        Args:
            name: 工具名称
            func: 工具函数
            description: 工具描述
            schema: 参数校验 schema（可选）
            
        Example:
            tools = ToolRegistry()
            tools.register("calculator", lambda expr: eval(expr))
        """
        tool = Tool(name=name, func=func, description=description)
        self._tools[name] = tool
        
        if self.validator and schema:
            self.validator.register_schema(name, schema)
    
    def register_tool(self, tool: Tool) -> None:
        """
        完整注册
        
        Args:
            tool: Tool 对象
            
        Example:
            tool = Tool(name="search", func=search_func, description="搜索")
            tools.register_tool(tool)
        """
        self._tools[tool.name] = tool
    
    def tool(self, name: str = None, description: str = "", **kwargs):
        """
        装饰器注册（推荐）
        
        Args:
            name: 工具名称（默认使用函数名）
            description: 工具描述
            **kwargs: 传递给 Tool 的其他参数
            
        Example:
            @tools.tool
            def search(query: str): ...
            
            @tools.tool(description="搜索")
            def search(query: str): ...
        """
        # 支持 @registry.tool (无括号)
        if callable(name):
            func = name
            tool_name = func.__name__
            # 这里的 description 和 kwargs 应该是空的或默认值
            tool = Tool(name=tool_name, func=func, description=description, **kwargs)
            self._tools[tool_name] = tool
            return func

        def decorator(func):
            tool_name = name or func.__name__
            tool = Tool(name=tool_name, func=func, description=description, **kwargs)
            self._tools[tool_name] = tool
            return func
        return decorator
    
    def call(self, name: str, params: Dict[str, Any]) -> str:
        """
        调用工具
        
        Args:
            name: 工具名称
            params: 参数字典
            
        Returns:
            工具执行结果（字符串）
        """
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"
        
        if not tool.enabled:
            return f"Error: Tool '{name}' is disabled"
        
        try:
            # Validate if validator is enabled
            if self.validator:
                    self.validator.validate(name, params)
            
            result = tool.call(**params)
            return str(result)
        except ValidationError as e:
            return f"Validation Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具定义"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())
    
    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        """获取所有工具的 Schema"""
        return {name: tool.get_schema() for name, tool in self._tools.items()}
    
    def enable_tool(self, name: str) -> bool:
        """启用工具"""
        tool = self._tools.get(name)
        if tool:
            tool.enabled = True
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """禁用工具"""
        tool = self._tools.get(name)
        if tool:
            tool.enabled = False
            return True
        return False
    
    def set_validation_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """Set validation schema for tool"""
        if self.validator:
            self.validator.register_schema(name, schema)
    
    def blacklist_tool(self, name: str) -> None:
        """Blacklist tool (prevent execution)"""
        if self.validator:
            self.validator.blacklist_tool(name)

