"""Prompt Template - 提示词模板管理"""
from typing import Dict, Any, Optional
import os


class PromptTemplate:
    """提示词模板加载与渲染"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化模板管理器
        
        Args:
            prompts_dir: 模板文件目录，默认为 core/context/prompts
        """
        if prompts_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompts_dir = os.path.join(current_dir, "prompts")
        
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, str] = {}
    
    def load(self, agent_type: str) -> str:
        """
        加载指定 Agent 类型的模板
        
        Args:
            agent_type: Agent 类型 (simple/react/planner/executor)
            
        Returns:
            模板内容
        """
        # 标准化 agent_type
        agent_type = agent_type.lower().replace("agent", "")
        
        # 检查缓存
        if agent_type in self._cache:
            return self._cache[agent_type]
        
        # 构建文件路径
        filename = f"agent_{agent_type}.txt"
        filepath = os.path.join(self.prompts_dir, filename)
        
        # 读取文件
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template = f.read()
            self._cache[agent_type] = template
            return template
        except FileNotFoundError:
            # 返回默认模板
            return self._get_default_template(agent_type)
    
    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """
        渲染模板（替换变量）
        
        Args:
            template: 模板字符串
            variables: 变量字典（所有变量应该都有默认值）
            
        Returns:
            渲染后的字符串
        """
        result = template
        
        # 替换变量（空字符串也会替换，清除占位符）
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value) if value else "")
        
        # 清理多余的空行
        import re
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
    
    def _get_default_template(self, agent_type: str) -> str:
        """获取默认模板（当文件不存在时）"""
        defaults = {
            "simple": "你是一个有帮助的助手。\n\n{tools}\n{skills}\n{memory_summary}",
            "react": "你是一个 ReAct Agent。\n\n{tools}\n{skills}\n{memory_summary}",
            "planner": "你是一个任务规划专家。\n\n{skills}\n{memory_summary}",
            "executor": "你是一个任务执行专家。\n\n{skills}\n{memory_summary}"
        }
        return defaults.get(agent_type, "你是一个助手。")

