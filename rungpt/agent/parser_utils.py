"""Enhanced ReAct Parser - 增强版解析器，支持 JSON 修复和模糊匹配"""
import re
import json
from typing import Optional, Dict, Any


def repair_json(json_str: str) -> str:
    """
    修复常见的 JSON 格式错误
    
    - 移除注释（// 和 /* */）
    - 修复单引号为双引号
    - 移除尾随逗号
    - 修复未引用的键
    """
    # 移除单行注释
    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
    
    # 移除多行注释
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    
    # 移除尾随逗号
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # 修复单引号为双引号（简单版本）
    # 注意：这个方法不完美，但能处理大多数情况
    json_str = json_str.replace("'", '"')
    
    # 尝试修复未引用的键（如 {key: "value"} -> {"key": "value"}）
    json_str = re.sub(r'(\{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
    
    return json_str


def fuzzy_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    模糊解析 JSON，尝试多种方式提取和修复
    
    1. 直接解析
    2. 提取 JSON 代码块
    3. 修复后解析
    4. 使用正则提取键值对
    """
    # 尝试 1: 直接解析
    try:
        return json.loads(text)
    except:
        pass
    
    # 尝试 2: 提取 JSON 代码块
    json_block_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if json_block_match:
        try:
            return json.loads(json_block_match.group(1))
        except:
            pass
    
    # 尝试 3: 修复后解析
    try:
        repaired = repair_json(text)
        return json.loads(repaired)
    except:
        pass
    
    # 尝试 4: 查找第一个 { } 包裹的内容
    brace_match = re.search(r'\{[^{}]*\}', text)
    if brace_match:
        try:
            repaired = repair_json(brace_match.group(0))
            return json.loads(repaired)
        except:
            pass
    
    # 尝试 5: 使用正则提取键值对（最后的手段）
    result = {}
    # 匹配 "key": "value" 或 key: "value"
    for match in re.finditer(r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']', text):
        result[match.group(1)] = match.group(2)
    
    return result if result else None


def extract_action_robust(text: str) -> Optional[tuple]:
    """
    健壮地提取 Action 名称和参数
    
    Returns:
        (action_name, params_dict) 或 None
    """
    # 模式 1: Action: tool_name[params]
    match = re.search(r'Action:\s*(\w+)\s*\[([^\]]*)\]', text, re.IGNORECASE)
    if match:
        name = match.group(1)
        params_str = match.group(2).strip()
        
        # 尝试解析参数
        if not params_str:
            return (name, {})
        
        # 如果参数看起来像 JSON
        if params_str.startswith('{'):
            params = fuzzy_parse_json(params_str)
            if params:
                return (name, params)
        
        # 否则作为单个参数
        return (name, {"input": params_str})
    
    # 模式 2: Action: tool_name(params)
    match = re.search(r'Action:\s*(\w+)\s*\(([^)]*)\)', text, re.IGNORECASE)
    if match:
        name = match.group(1)
        params_str = match.group(2).strip()
        
        if not params_str:
            return (name, {})
        
        # 尝试解析为 JSON
        params = fuzzy_parse_json('{' + params_str + '}')
        if params:
            return (name, params)
        
        # 尝试解析为 key=value 格式
        params = {}
        for part in params_str.split(','):
            if '=' in part:
                key, val = part.split('=', 1)
                params[key.strip()] = val.strip().strip('"\'')
        
        if params:
            return (name, params)
        
        return (name, {"input": params_str})
    
    # 模式 3: 直接的工具名（无参数）
    match = re.search(r'Action:\s*(\w+)\s*$', text, re.IGNORECASE | re.MULTILINE)
    if match:
        return (match.group(1), {})
    
    return None
