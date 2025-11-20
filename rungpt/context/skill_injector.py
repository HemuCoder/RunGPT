"""Skill Injector - 技能注入器"""
from typing import List, Optional


class SkillInjector:
    """技能描述注入器"""
    
    def generate(self, skills: Optional[List[str]]) -> str:
        """
        生成技能描述文本
        
        Args:
            skills: 技能描述列表
            
        Returns:
            格式化的技能描述
        """
        if not skills:
            return ""
        
        desc = "你的能力：\n"
        for skill in skills:
            desc += f"  - {skill}\n"
        
        return desc.strip()

