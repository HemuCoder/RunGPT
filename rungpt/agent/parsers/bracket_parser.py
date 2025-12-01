"""Bracket Format Parser - 解析方括号格式"""
import re
from typing import Optional
from .strategy import ParserStrategy, Action


class BracketFormatParser(ParserStrategy):
    """
    解析方括号格式: tool_name[input] 或 Finish[answer]
    
    支持格式:
        - Action: calculator[10+20]
        - Action: search[深圳天气]
        - Action: Finish[结果是30]
        - Finish[结果是30]  (兼容无 Action: 前缀)
    """
    
    # 参数名映射:根据工具名推断参数名
    PARAM_MAP = {
        'calculator': 'expression',
        'search': 'query',
        'weather': 'city',
    }
    
    def can_handle(self, text: str) -> bool:
        """检查是否包含方括号格式"""
        return bool(re.search(r'\w+\[.*?\]', text))
    
    def parse(self, text: str) -> Optional[Action]:
        """解析方括号格式"""
        # 匹配 Action: xxx[yyy] 或直接 xxx[yyy]
        patterns = [
            r'Action:\s*(\w+)\[(.*?)\]',  # 标准格式
            r'(?:^|\n)(\w+)\[(.*?)\]'      # 无前缀格式
        ]
        
        match = None
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                break
        
        if not match:
            return None
        
        name = match.group(1).strip()
        input_text = match.group(2).strip()
        
        # Finish action 特殊处理
        if name.lower() == 'finish':
            return Action(
                name="FINISH",
                params={"answer": input_text},
                raw=match.group(0)
            )
        
        # 普通工具调用:解析参数
        params = self._parse_params(name, input_text)
        return Action(name=name, params=params, raw=match.group(0))
    
    def _parse_params(self, tool_name: str, input_text: str) -> dict:
        """
        解析参数
        
        支持两种格式:
        1. key=value, key2=value2
        2. 单个值(自动推断参数名)
        """
        params = {}
        
        # 尝试解析 key=value 格式
        if '=' in input_text:
            # 正则匹配: key="value" 或 key='value' 或 key=value
            # Group 1: key
            # Group 2: 双引号值
            # Group 3: 单引号值
            # Group 4: 无引号值(不含逗号)
            pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^,]+))'
            
            matches = list(re.finditer(pattern, input_text))
            if matches:
                for match in matches:
                    key = match.group(1)
                    # 获取非空的捕获组作为值
                    val = match.group(2)
                    if val is None:
                        val = match.group(3)
                    if val is None:
                        val = match.group(4)
                    
                    if val is not None:
                        params[key.strip()] = val.strip()
                return params
        
        # 单个参数:推断参数名
        if not params:
            param_name = self.PARAM_MAP.get(tool_name.lower(), 'input')
            params[param_name] = input_text
        
        return params
