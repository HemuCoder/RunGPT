"""Robust Action Parser - 模糊匹配和 JSON 修复"""
import re
import json
from typing import Optional
from .strategy import ParserStrategy, Action


class RobustActionParser(ParserStrategy):
    """
    健壮解析器:模糊匹配和 JSON 修复
    
    作为最后的手段,尝试修复和提取格式错误的 Action
    """
    
    def can_handle(self, text: str) -> bool:
        """总是尝试处理(作为兜底策略)"""
        return 'Action:' in text or 'action' in text.lower()
    
    def parse(self, text: str) -> Optional[Action]:
        """模糊解析"""
        # 模式 1: Action: tool_name[params]
        result = self._parse_bracket_fuzzy(text)
        if result:
            return result
        
        # 模式 2: Action: tool_name(params)
        result = self._parse_function_fuzzy(text)
        if result:
            return result
        
        return None
    
    def _parse_bracket_fuzzy(self, text: str) -> Optional[Action]:
        """模糊解析方括号格式"""
        match = re.search(r'Action:\s*(\w+)\s*\[([^\]]*)\]', text, re.IGNORECASE)
        if not match:
            return None
        
        name = match.group(1)
        params_str = match.group(2).strip()
        
        if not params_str:
            return Action(name, {}, match.group(0))
        
        # 尝试解析为 JSON
        if params_str.startswith('{'):
            params = self._fuzzy_parse_json(params_str)
            if params:
                return Action(name, params, match.group(0))
        
        # 作为单个参数
        return Action(name, {"input": params_str}, match.group(0))
    
    def _parse_function_fuzzy(self, text: str) -> Optional[Action]:
        """模糊解析函数格式"""
        match = re.search(r'Action:\s*(\w+)\s*\(([^)]*)\)', text, re.IGNORECASE)
        if not match:
            return None
        
        name = match.group(1)
        params_str = match.group(2).strip()
        
        if not params_str:
            return Action(name, {}, match.group(0))
        
        # 尝试解析为 JSON
        params = self._fuzzy_parse_json('{' + params_str + '}')
        if params:
            return Action(name, params, match.group(0))
        
        # 尝试 key=value 格式
        params = {}
        for part in params_str.split(','):
            if '=' in part:
                key, val = part.split('=', 1)
                params[key.strip()] = val.strip().strip('"\'')
        
        if params:
            return Action(name, params, match.group(0))
        
        return Action(name, {"input": params_str}, match.group(0))
    
    def _fuzzy_parse_json(self, text: str) -> Optional[dict]:
        """
        模糊解析 JSON
        
        尝试修复常见错误:
        - 单引号 -> 双引号
        - 尾随逗号
        - 注释
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 修复后解析
        try:
            repaired = self._repair_json(text)
            return json.loads(repaired)
        except:
            pass
        
        return None
    
    def _repair_json(self, json_str: str) -> str:
        """修复常见 JSON 错误"""
        # 移除单行注释
        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
        
        # 移除多行注释
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # 移除尾随逗号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 单引号 -> 双引号
        json_str = json_str.replace("'", '"')
        
        # 修复未引用的键
        json_str = re.sub(r'(\{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        return json_str
