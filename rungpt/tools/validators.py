"""Validators - Tool parameter validation"""
from typing import Dict, Any, List, Optional, Callable


class ValidationError(Exception):
    """Validation error"""
    pass


class Validator:
    """Parameter validator"""
    
    @staticmethod
    def validate_required(params: Dict[str, Any], required: List[str]) -> None:
        """Validate required parameters"""
        missing = [k for k in required if k not in params]
        if missing:
            raise ValidationError(f"Missing required params: {', '.join(missing)}")
    
    @staticmethod
    def validate_types(params: Dict[str, Any], types: Dict[str, type]) -> None:
        """Validate parameter types"""
        for key, expected_type in types.items():
            if key in params and not isinstance(params[key], expected_type):
                raise ValidationError(
                    f"Param {key} type error: expected {expected_type.__name__}, "
                    f"got {type(params[key]).__name__}"
                )
    
    @staticmethod
    def validate_range(value: float, min_val: Optional[float] = None, 
                      max_val: Optional[float] = None, name: str = "value") -> None:
        """Validate numeric range"""
        if min_val is not None and value < min_val:
            raise ValidationError(f"{name} must be >= {min_val}")
        if max_val is not None and value > max_val:
            raise ValidationError(f"{name} must be <= {max_val}")


class ToolValidator:
    """Tool call validator"""
    
    def __init__(self):
        self.validator = Validator()
        self.blacklist: List[str] = []
        self.schemas: Dict[str, Dict[str, Any]] = {}
    
    def register_schema(self, tool_name: str, schema: Dict[str, Any]) -> None:
        """Register tool parameter schema"""
        self.schemas[tool_name] = schema
    
    def blacklist_tool(self, tool_name: str) -> None:
        """Disable tool"""
        if tool_name not in self.blacklist:
            self.blacklist.append(tool_name)
    
    def whitelist_tool(self, tool_name: str) -> None:
        """Enable tool"""
        if tool_name in self.blacklist:
            self.blacklist.remove(tool_name)
    
    def validate(self, tool_name: str, params: Dict[str, Any]) -> None:
        """Validate tool call"""
        if tool_name in self.blacklist:
            raise ValidationError(f"Tool '{tool_name}' is disabled")
        
        if tool_name not in self.schemas:
            return
        
        schema = self.schemas[tool_name]
        
        # Required params
        if "required" in schema:
            self.validator.validate_required(params, schema["required"])
        
        # Type validation
        if "types" in schema:
            self.validator.validate_types(params, schema["types"])
        
        # Range validation
        if "ranges" in schema:
            for param_name, (min_val, max_val) in schema["ranges"].items():
                if param_name in params:
                    self.validator.validate_range(
                        params[param_name], min_val, max_val, param_name
                    )
