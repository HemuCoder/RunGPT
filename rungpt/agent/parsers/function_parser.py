"""Function Call Parser - 解析函数调用格式"""
import re
import json
from typing import Optional
from .strategy import ParserStrategy, Action


class FunctionCallParser(ParserStrategy):
    """
    解析函数调用格式
    
    支持格式:
        - Action: func(a="value", b=123)
        - Action: func()
        - Action: func({'a': 'value'})
    """
    
    def can_handle(self, text: str) -> bool:
        """检查是否包含函数调用格式"""
        return bool(re.search(r'Action:\s*\w+\(', text, re.IGNORECASE))
    
    def parse(self, text: str) -> Optional[Action]:
        """解析函数调用格式"""
        # 查找 Action: func_name(
        action_match = re.search(r'Action:\s*(\w+)\(', text, re.IGNORECASE)
        if not action_match:
            # 尝试无括号格式
            match = re.search(r'Action:\s*(\w+)(?:\s|$)', text, re.IGNORECASE)
            if match:
                return Action(match.group(1), {}, match.group(0).strip())
            return None
        
        name = action_match.group(1)
        start_pos = action_match.end() - 1  # 指向 '('
        end_pos = self._find_matching_paren(text, start_pos)
        
        if end_pos == -1:
            return None
        
        params_str = text[start_pos+1:end_pos].strip()
        params = self._parse_params(params_str)
        
        return Action(
            name=name,
            params=params,
            raw=text[action_match.start():end_pos+1]
        )
    
    def _find_matching_paren(self, text: str, start: int) -> int:
        """找到匹配的右括号"""
        count = 0
        for i in range(start, len(text)):
            if text[i] == '(':
                count += 1
            elif text[i] == ')':
                count -= 1
                if count == 0:
                    return i
        return -1
    
    def _parse_params(self, params_str: str) -> dict:
        """
        解析参数字符串
        
        支持:
        1. 字典格式: {'key': 'value'}
        2. 函数参数格式: key="value", key2=123
        """
        if not params_str:
            return {}
        
        # 字典格式
        if params_str.startswith('{'):
            try:
                # 尝试 eval (支持 Python 字典)
                result = eval(params_str)
                if isinstance(result, dict):
                    return result
            except:
                pass
            
            try:
                # 尝试 JSON
                normalized = params_str.replace("'", '"')
                return json.loads(normalized)
            except:
                return {}
        
        # 函数参数格式: key=value
        params = {}
        pattern = r'(\w+)=(?:(["\'])(.*?)\2|([^\s,]+))'
        
        for match in re.finditer(pattern, params_str):
            key = match.group(1)
            # 优先取带引号的值,否则取不带引号的值
            value = match.group(3) if match.group(2) else match.group(4)
            
            # 尝试转换数字
            if value:
                try:
                    if '.' not in value:
                        params[key] = int(value)
                    else:
                        params[key] = float(value)
                except ValueError:
                    params[key] = value
        
        return params
