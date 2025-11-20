"""ReAct Parser - 解析模型输出中的 Action"""
import re
from typing import Optional, Dict, Any, List
import json


class Action:
    """执行动作"""
    
    def __init__(self, name: str, params: Dict[str, Any], raw: str = ""):
        self.name = name
        self.params = params
        self.raw = raw
    
    def __repr__(self) -> str:
        return f"Action(name={self.name}, params={self.params})"


class ReActParser:
    """解析 ReAct 格式的模型输出"""
    
    @staticmethod
    def parse(text: str) -> Optional[Action]:
        """
        解析 Action
        
        支持格式：
        1. Action: tool_name[input]
        2. Action: Finish[answer]
        3. Action: tool_name(param="value") (legacy)
        
        Args:
            text: 模型输出文本
            
        Returns:
            Action 对象或 None
        """
        # 新格式：tool_name[input]
        action = ReActParser._parse_bracket_format(text)
        if action:
            return action
        
        # 旧格式兼容
        action = ReActParser._parse_function_call(text)
        if action:
            return action
        
        action = ReActParser._parse_json_action(text)
        if action:
            return action
        
        return None
    
    @staticmethod
    def _parse_bracket_format(text: str) -> Optional[Action]:
        """
        解析方括号格式: tool_name[input] 或 Finish[answer]
        
        Examples:
            Action: calculator[10+20]
            Action: search[深圳天气]
            Action: Finish[结果是30]
            Finish[结果是30]  (兼容无 Action: 前缀)
        """
        import re
        
        # 匹配 Action: xxx[yyy] 或直接 xxx[yyy]（兼容模型省略 Action:）
        patterns = [
            r'Action:\s*(\w+)\[(.*?)\]',  # 标准格式
            r'(?:^|\n)(\w+)\[(.*?)\]'      # 无前缀格式（行首或换行后）
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                break
        
        if not match:
            return None
        
        name = match.group(1).strip()
        input_text = match.group(2).strip()
        
        # 如果是 Finish，标记为特殊 action
        if name.lower() == 'finish':
            return Action(name="FINISH", params={"answer": input_text}, raw=match.group(0))
        
        # 普通工具调用，input 作为唯一参数
        # 尝试解析是否有多个参数（如 key=value 格式）
        params = {}
        if '=' in input_text:
            # 尝试解析 key=value 格式
            for part in input_text.split(','):
                if '=' in part:
                    key, val = part.split('=', 1)
                    params[key.strip()] = val.strip().strip('"\'')
        
        if not params:
            # 单个参数，猜测参数名
            # 尝试从工具名推断（如 calculator -> expression, search -> query）
            param_map = {
                'calculator': 'expression',
                'search': 'query',
                'weather': 'city',
            }
            param_name = param_map.get(name.lower(), 'input')
            params[param_name] = input_text
        
        return Action(name=name, params=params, raw=match.group(0))
    
    @staticmethod
    def _parse_function_call(text: str) -> Optional[Action]:
        """
        解析函数调用格式
        
        支持格式：
        1. Action: func(a="value", b=123)  # 带引号或不带引号
        2. Action: func()                   # 无参数
        3. Action: func({'a': 'value'})     # 字典格式
        """
        # 找到 Action: 后面的内容
        action_match = re.search(r'Action:\s*(\w+)\(', text, re.IGNORECASE)
        if not action_match:
            # 尝试无括号格式
            pattern_no_parens = r'Action:\s*(\w+)(?:\s|$)'
            match = re.search(pattern_no_parens, text, re.IGNORECASE)
            if match:
                return Action(match.group(1), {}, match.group(0).strip())
            return None
        
        name = action_match.group(1)
        start_pos = action_match.end() - 1  # 指向 '('
        end_pos = ReActParser._find_matching_paren(text, start_pos)
        
        if end_pos == -1:
            # 没找到匹配的右括号
            return None
        
        params_str = text[start_pos+1:end_pos].strip()
        
        params = {}
        if params_str:
            # 尝试解析为字典格式 {'key': 'value'}
            if params_str.startswith('{'):
                try:
                    # 使用 eval 来解析 Python 字典（更宽松）
                    params = eval(params_str)
                    if not isinstance(params, dict):
                        params = {}
                except (SyntaxError, ValueError, NameError):
                    # 如果 eval 失败，尝试 JSON
                    try:
                        params_str_normalized = params_str.replace("'", '"')
                        params = json.loads(params_str_normalized)
                    except json.JSONDecodeError:
                        params = {}
            else:
                # 解析函数参数格式 key=value
                # 支持：key="value" 或 key='value' 或 key=123
                param_pattern = r'(\w+)=(?:(["\'])(.*?)\2|([^\s,]+))'
                for param_match in re.finditer(param_pattern, params_str):
                    key = param_match.group(1)
                    # 优先取带引号的值，否则取不带引号的值
                    value = param_match.group(3) if param_match.group(2) else param_match.group(4)
                    
                    # 尝试转换数字类型
                    if value:
                        try:
                            # 尝试转为整数
                            if '.' not in value:
                                params[key] = int(value)
                            else:
                                params[key] = float(value)
                        except ValueError:
                            # 保持为字符串
                            params[key] = value
        
        return Action(name, params, text[action_match.start():end_pos+1])
    
    @staticmethod
    def _find_matching_paren(text: str, start: int) -> int:
        """找到匹配的右括号位置"""
        count = 0
        for i in range(start, len(text)):
            if text[i] == '(':
                count += 1
            elif text[i] == ')':
                count -= 1
                if count == 0:
                    return i
        return -1
    
    @staticmethod
    def _parse_json_action(text: str) -> Optional[Action]:
        """解析 JSON 格式的 action"""
        pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(pattern, text, re.DOTALL)
        
        if not match:
            return None
        
        try:
            data = json.loads(match.group(1))
            if "action" in data:
                return Action(
                    data["action"],
                    data.get("params", {}),
                    match.group(0)
                )
        except json.JSONDecodeError:
            pass
        
        return None
    
    @staticmethod
    def has_finish(text: str) -> bool:
        """检查是否包含完成标记"""
        finish_patterns = [
            r'Action:\s*Finish\[',
            r'(?:^|\n)Finish\[',  # 兼容无 Action: 前缀
            r'Action:\s*FINISH',
            r'"action":\s*"FINISH"',
            r'Final Answer:',
            r'最终答案：'
        ]
        return any(re.search(p, text, re.IGNORECASE | re.MULTILINE) for p in finish_patterns)
    
    @staticmethod
    def extract_thought(text: str) -> Optional[str]:
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
    
    @staticmethod
    def extract_observation(text: str) -> Optional[str]:
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

