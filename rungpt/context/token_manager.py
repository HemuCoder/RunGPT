"""Token Manager - Token 管理与裁剪"""
from typing import List, Dict


class TokenManager:
    """简单的 Token 管理器"""
    
    def truncate(
        self, 
        messages: List[Dict[str, str]], 
        max_messages: int = 50
    ) -> List[Dict[str, str]]:
        """
        裁剪消息列表（简单策略：保留 system + 最近N条）
        
        Args:
            messages: 消息列表
            max_messages: 最大消息数
            
        Returns:
            裁剪后的消息列表
        """
        if len(messages) <= max_messages:
            return messages
        
        # 分离 system 消息和其他消息
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        # 保留最近的消息
        keep_count = max_messages - len(system_msgs)
        if keep_count > 0:
            other_msgs = other_msgs[-keep_count:]
        
        return system_msgs + other_msgs
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算 token 数量（粗略估算：1 token ≈ 4 字符）
        
        Args:
            text: 文本内容
            
        Returns:
            估算的 token 数
        """
        return len(text) // 4

