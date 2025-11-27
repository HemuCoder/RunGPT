"""JSON Action Parser - 解析 JSON 代码块格式"""
import re
import json
from typing import Optional
from .strategy import ParserStrategy, Action


class JSONActionParser(ParserStrategy):
    """
    解析 JSON 代码块格式
    
    支持格式:
        ```json
        {
            "action": "tool_name",
            "params": {"key": "value"}
        }
        ```
    """
    
    def can_handle(self, text: str) -> bool:
        """检查是否包含 JSON 代码块"""
        return '```json' in text or '```' in text
    
    def parse(self, text: str) -> Optional[Action]:
        """解析 JSON 代码块"""
        pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(pattern, text, re.DOTALL)
        
        if not match:
            # 尝试无语言标识的代码块
            pattern = r'```\s*\n(.*?)\n```'
            match = re.search(pattern, text, re.DOTALL)
        
        if not match:
            return None
        
        try:
            data = json.loads(match.group(1))
            if "action" in data:
                return Action(
                    name=data["action"],
                    params=data.get("params", {}),
                    raw=match.group(0)
                )
        except json.JSONDecodeError:
            pass
        
        return None
