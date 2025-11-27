"""ReAct Parser - 解析模型输出中的 Action"""
from typing import Optional
from .parsers import ParserManager, Action as ParsedAction


# 向后兼容:导出 Action 类
class Action:
    """执行动作（向后兼容包装）"""
    
    def __init__(self, name: str, params: dict, raw: str = ""):
        self.name = name
        self.params = params
        self.raw = raw
    
    def __repr__(self) -> str:
        return f"Action(name={self.name}, params={self.params})"


class ReActParser:
    """
    ReAct 格式解析器
    
    使用策略模式支持多种格式:
    1. Action: tool_name[input]
    2. Action: tool_name(param="value")
    3. Action: tool_name{"key": "value"}
    4. Action: Finish[answer]

    """
    
    def __init__(self):
        """初始化解析器管理器"""
        self._manager = ParserManager()
    
    @staticmethod
    def parse(text: str) -> Optional[Action]:
        """
        解析 Action（策略模式版本）
        
        Args:
            text: 模型输出文本
            
        Returns:
            Action 对象或 None
        """
        parser = ReActParser()
        return parser._parse(text)
    
    def _parse(self, text: str) -> Optional[Action]:
        """内部解析方法"""
        parsed = self._manager.parse(text)
        if parsed:
            # 转换为向后兼容的 Action 类
            return Action(parsed.name, parsed.params, parsed.raw)
        return None

    
    @staticmethod
    def has_finish(text: str) -> bool:
        """检查是否包含完成标记"""
        parser = ReActParser()
        return parser._manager.has_finish(text)
    
    @staticmethod
    def extract_thought(text: str) -> Optional[str]:
        """提取思考过程"""
        parser = ReActParser()
        return parser._manager.extract_thought(text)
    
    @staticmethod
    def extract_observation(text: str) -> Optional[str]:
        """提取观察结果"""
        parser = ReActParser()
        return parser._manager.extract_observation(text)

