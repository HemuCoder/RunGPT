"""Parser Manager - 策略编排器"""
import re
from typing import List, Optional
from .strategy import ParserStrategy, Action
from .bracket_parser import BracketFormatParser
from .function_parser import FunctionCallParser
from .json_parser import JSONActionParser
from .robust_parser import RobustActionParser


class ParserManager:
    """
    解析器管理器:编排多个解析策略
    
    按优先级尝试不同的解析器,直到成功
    """
    
    def __init__(self, strategies: Optional[List[ParserStrategy]] = None):
        """
        初始化解析器管理器
        
        Args:
            strategies: 解析策略列表(按优先级排序)
                       默认使用标准策略组合
        """
        if strategies is None:
            # 默认策略:按优先级排序
            self.strategies = [
                BracketFormatParser(),    # 最常用
                FunctionCallParser(),     # 次常用
                JSONActionParser(),       # 结构化格式
                RobustActionParser(),     # 兜底策略
            ]
        else:
            self.strategies = strategies
    
    def parse(self, text: str) -> Optional[Action]:
        """
        解析文本,提取 Action
        
        按策略优先级依次尝试,返回第一个成功的结果
        
        Args:
            text: 模型输出文本
            
        Returns:
            Action 对象或 None
        """
        for strategy in self.strategies:
            # 快速检查:避免无效尝试
            if not strategy.can_handle(text):
                continue
            
            # 尝试解析
            action = strategy.parse(text)
            if action:
                # 处理 FINISH action
                if action.name.upper() == "FINISH":
                    return self._normalize_finish_action(action)
                return action
        
        return None
    
    def _normalize_finish_action(self, action: Action) -> Action:
        """
        标准化 FINISH action
        
        确保参数格式统一为 {"answer": "..."}
        """
        params = action.params
        
        # 已经是标准格式
        if "answer" in params:
            return Action("FINISH", params, action.raw)
        
        # 转换 {"input": "..."} 格式
        if "input" in params:
            return Action("FINISH", {"answer": params["input"]}, action.raw)
        
        # 其他情况:将整个 params 转为字符串
        return Action("FINISH", {"answer": str(params)}, action.raw)
    
    def has_finish(self, text: str) -> bool:
        """检查是否包含完成标记"""
        finish_patterns = [
            r'Action:\s*Finish\[',
            r'(?:^|\n)Finish\[',
            r'Action:\s*FINISH',
            r'"action":\s*"FINISH"',
            r'Final Answer:',
            r'最终答案：'
        ]
        return any(re.search(p, text, re.IGNORECASE | re.MULTILINE) for p in finish_patterns)
    
    def extract_thought(self, text: str) -> Optional[str]:
        """提取思考过程"""
        patterns = [
            r'Thought:\s*(.*?)(?=\n|Action:|$)',
            r'思考：\s*(.*?)(?=\n|Action:|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_observation(self, text: str) -> Optional[str]:
        """提取观察结果"""
        patterns = [
            r'Observation:\s*(.*?)(?=\n|Thought:|$)',
            r'观察：\s*(.*?)(?=\n|Thought:|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
