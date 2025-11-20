"""Thread - 对话线程管理器"""
from typing import List, Dict, Optional, Any
from datetime import datetime


class Thread:
    """轻量级对话线程，维护消息历史和上下文"""
    
    def __init__(self, thread_id: Optional[str] = None):
        self.id = thread_id or self._gen_id()
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()
    
    def _gen_id(self) -> str:
        """生成线程ID"""
        return f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """
        添加消息
        
        Args:
            role: 消息角色 (user/assistant/system/tool)
            content: 消息内容
            **kwargs: 其他元数据
        """
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.messages.append(msg)
    
    def add_user(self, content: str, **kwargs) -> None:
        """添加用户消息"""
        self.add_message("user", content, **kwargs)
    
    def add_assistant(self, content: str, **kwargs) -> None:
        """添加助手消息"""
        self.add_message("assistant", content, **kwargs)
    
    def add_system(self, content: str, **kwargs) -> None:
        """添加系统消息"""
        self.add_message("system", content, **kwargs)
    
    def add_tool(self, content: str, tool_name: str, **kwargs) -> None:
        """添加工具调用消息"""
        self.add_message("tool", content, tool_name=tool_name, **kwargs)
    
    def get_messages(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取消息列表
        
        Args:
            role: 可选，筛选指定角色的消息
            
        Returns:
            消息列表
        """
        if role:
            return [m for m in self.messages if m.get("role") == role]
        return self.messages.copy()
    
    def get_context(self, max_msgs: Optional[int] = None) -> List[Dict[str, str]]:
        """
        获取适用于模型的上下文（仅包含 role 和 content）
        
        Args:
            max_msgs: 最大消息数量（最近的N条）
            
        Returns:
            格式化的消息列表
        """
        msgs = self.messages[-max_msgs:] if max_msgs else self.messages
        return [{"role": m["role"], "content": m["content"]} for m in msgs]
    
    def clear(self) -> None:
        """清空消息历史"""
        self.messages.clear()
    
    def set_meta(self, key: str, value: Any) -> None:
        """设置元数据"""
        self.metadata[key] = value
    
    def get_meta(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "id": self.id,
            "messages": self.messages,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Thread":
        """从字典恢复"""
        thread = cls(thread_id=data["id"])
        thread.messages = data["messages"]
        thread.metadata = data["metadata"]
        thread.created_at = datetime.fromisoformat(data["created_at"])
        return thread
    
    def __len__(self) -> int:
        """返回消息数量"""
        return len(self.messages)
    
    def __repr__(self) -> str:
        return f"Thread(id={self.id}, messages={len(self.messages)})"

