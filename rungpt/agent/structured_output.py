"""Structured Output - Pydantic 结构化输出支持"""
from typing import Type, TypeVar, Optional, Any, Dict
from pydantic import BaseModel
import json
import re

T = TypeVar("T", bound=BaseModel)

class StructuredOutputManager:
    """结构化输出管理器"""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
        self.schema = model_class.model_json_schema()
    
    def get_format_instruction(self) -> str:
        """获取格式说明提示词"""
        schema_json = json.dumps(self.schema, ensure_ascii=False, indent=2)
        return f"""
请务必输出符合以下 JSON Schema 的 JSON 格式数据:
```json
{schema_json}
```
不要输出任何其他解释性文字,只输出 JSON 代码块。
"""

    def parse_response(self, response: str) -> T:
        """解析模型响应为 Pydantic 对象"""
        # 1. 尝试提取 JSON 代码块
        json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析(可能没有代码块标记)
            json_str = response.strip()
            
        try:
            data = json.loads(json_str)
            return self.model_class.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            # 简单的错误恢复:尝试修复常见的 JSON 错误(如单引号)
            try:
                # 替换单引号为双引号(非完美,但在简单场景有效)
                fixed_json = json_str.replace("'", '"')
                data = json.loads(fixed_json)
                return self.model_class.model_validate(data)
            except Exception:
                raise ValueError(f"无法解析结构化输出: {e}\n原始响应: {response}")

def extract_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """提取 JSON Schema (辅助函数)"""
    return model.model_json_schema()
