"""Tool Result - 标准化工具返回对象"""
from dataclasses import dataclass
from typing import Any, Optional
import json


@dataclass
class ToolResult:
    """
    标准化的工具返回对象
    
    Attributes:
        success: 是否成功
        data: 返回数据
        error: 错误信息（失败时）
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    
    def __str__(self) -> str:
        """转换为 LLM 友好的字符串格式"""
        if self.success:
            if isinstance(self.data, (dict, list)):
                return json.dumps({"success": True, "data": self.data}, ensure_ascii=False, indent=2)
            return f"Success: {self.data}"
        return f"Error: {self.error}"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        result = {"success": self.success}
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error
        return result
    
    @classmethod
    def ok(cls, data: Any = None) -> "ToolResult":
        """创建成功结果"""
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        """创建失败结果"""
        return cls(success=False, error=error)
