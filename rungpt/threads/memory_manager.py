"""Memory Manager - 记忆管理器"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from .thread import Thread


class Memory:
    """单个记忆单元"""
    
    def __init__(self, key: str, value: Any, category: str = "default"):
        self.key = key
        self.value = value
        self.category = category
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update(self, value: Any) -> None:
        """更新记忆值"""
        self.value = value
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class MemoryManager:
    """记忆管理器 - 维护短期任务记忆"""
    
    def __init__(self, max_memories: int = 1000, max_threads: int = 100):
        self.memories: Dict[str, Memory] = {}
        self.thread_history: Dict[str, Thread] = {}
        self.max_memories = max_memories
        self.max_threads = max_threads
    
    def store(self, key: str, value: Any, category: str = "default") -> None:
        """
        存储记忆
        
        Args:
            key: 记忆键
            value: 记忆值
            category: 记忆分类
        """
        if key in self.memories:
            self.memories[key].update(value)
        else:
            if len(self.memories) >= self.max_memories:
                oldest = min(self.memories.values(), key=lambda m: m.updated_at)
                del self.memories[oldest.key]
            self.memories[key] = Memory(key, value, category)
    
    def recall(self, key: str, default: Any = None) -> Any:
        """
        回忆记忆
        
        Args:
            key: 记忆键
            default: 默认值
            
        Returns:
            记忆值
        """
        mem = self.memories.get(key)
        return mem.value if mem else default
    
    def recall_by_category(self, category: str) -> Dict[str, Any]:
        """
        按分类回忆记忆
        
        Args:
            category: 记忆分类
            
        Returns:
            该分类下的所有记忆
        """
        return {
            k: m.value 
            for k, m in self.memories.items() 
            if m.category == category
        }
    
    def forget(self, key: str) -> bool:
        """
        遗忘记忆
        
        Args:
            key: 记忆键
            
        Returns:
            是否成功遗忘
        """
        if key in self.memories:
            del self.memories[key]
            return True
        return False
    
    def clear(self, category: Optional[str] = None) -> None:
        """
        清空记忆
        
        Args:
            category: 可选，仅清空指定分类
        """
        if category:
            to_remove = [k for k, m in self.memories.items() if m.category == category]
            for k in to_remove:
                del self.memories[k]
        else:
            self.memories.clear()
    
    def save_thread(self, thread: Thread) -> None:
        """保存线程到历史"""
        if thread.id not in self.thread_history and len(self.thread_history) >= self.max_threads:
            oldest_id = min(self.thread_history.keys(), key=lambda tid: self.thread_history[tid].created_at)
            del self.thread_history[oldest_id]
        self.thread_history[thread.id] = thread
    
    def load_thread(self, thread_id: str) -> Optional[Thread]:
        """从历史加载线程"""
        return self.thread_history.get(thread_id)
    
    def list_threads(self) -> List[str]:
        """列出所有线程ID"""
        return list(self.thread_history.keys())
    
    def get_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        categories = {}
        for mem in self.memories.values():
            cat = mem.category
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_memories": len(self.memories),
            "categories": categories,
            "total_threads": len(self.thread_history)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "memories": {k: m.to_dict() for k, m in self.memories.items()},
            "thread_history": {k: t.to_dict() for k, t in self.thread_history.items()},
            "max_memories": self.max_memories,
            "max_threads": self.max_threads
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryManager":
        """从字典恢复"""
        max_memories = data.get("max_memories", 1000)
        max_threads = data.get("max_threads", 100)
        mgr = cls(max_memories=max_memories, max_threads=max_threads)
        
        for k, m_data in data.get("memories", {}).items():
            mem = Memory(m_data["key"], m_data["value"], m_data["category"])
            mem.created_at = datetime.fromisoformat(m_data["created_at"])
            mem.updated_at = datetime.fromisoformat(m_data["updated_at"])
            mgr.memories[k] = mem
        
        for k, t_data in data.get("thread_history", {}).items():
            mgr.thread_history[k] = Thread.from_dict(t_data)
        
        return mgr
    
    def __repr__(self) -> str:
        summary = self.get_summary()
        return f"MemoryManager(memories={summary['total_memories']}, threads={summary['total_threads']})"

