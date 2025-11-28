"""Agent Factory - 根据配置创建 Agent 实例"""
from typing import Dict, Any, Optional
from .agent_base import AgentBase, AgentProfile
from .simple_agent import SimpleAgent
from .react_agent import ReActAgent
from ..models import load_model
from ..threads import MemoryManager
from ..tools import ToolRegistry


class AgentFactory:
    """Agent 工厂，根据配置创建 Agent 实例"""
    
    AGENT_TYPES = {
        "simple": SimpleAgent,
        "react": ReActAgent,
    }
    
    @classmethod
    def create(
        cls,
        agent_type: str,
        profile: AgentProfile,
        model_config: Optional[Dict[str, Any]] = None,
        memory: Optional[MemoryManager] = None,
        tools: Optional[ToolRegistry] = None,
        stream: bool = False,
        verbose: bool = False,
        **kwargs
    ) -> AgentBase:
        """
        创建 Agent 实例
        
        Args:
            agent_type: Agent 类型 (simple/react/planner/executor)
            profile: Agent 配置
            model_config: 模型配置
            memory: 记忆管理器
            tools: 工具注册表（ReAct/Simple Agent 可选）
            stream: 是否启用流式输出
            verbose: 是否启用详细日志
            **kwargs: 其他参数
            
        Returns:
            Agent 实例
        """
        if agent_type not in cls.AGENT_TYPES:
            raise ValueError(f"未知 Agent 类型: {agent_type}. 可用类型: {list(cls.AGENT_TYPES.keys())}")
        
        model_config = model_config or {}
        model = load_model(
            provider=model_config.get("provider", "unified"),
            model_name=profile.model_name,
            **model_config.get("extra", {})
        )
        
        agent_class = cls.AGENT_TYPES[agent_type]
        
        # 从 profile 提取参数
        system_prompt = profile.extra.get("system_prompt", "你是一个有帮助的助手。")
        
        # 构造 Agent 参数
        agent_kwargs = {
            "name": profile.name,
            "temperature": profile.temperature,
            "max_steps": profile.max_steps,
            "memory": memory,
            "stream": stream,
            "verbose": verbose,
            **kwargs
        }
        
        # 创建 Agent（所有类型都支持 tools）
        return agent_class(
            system_prompt=system_prompt,
            model=model,
            tools=tools,
            **agent_kwargs
        )
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> AgentBase:
        """
        从配置字典创建 Agent
        
        Args:
            config: 配置字典，格式：
                {
                    "type": "simple",
                    "profile": {
                        "name": "MyAgent",
                        "model_name": "gpt-4o",
                        "max_steps": 10,
                        "temperature": 0.7
                    },
                    "model_config": {...},
                    "stream": True,
                    "verbose": True,
                    "tools": [...] (for react/simple)
                }
        
        Returns:
            Agent 实例
        """
        agent_type = config.get("type", "simple")
        profile_config = config.get("profile", {})
        
        profile = AgentProfile(**profile_config)
        
        model_config = config.get("model_config")
        memory = config.get("memory")
        stream = config.get("stream", False)
        verbose = config.get("verbose", False)
        
        tools = None
        if "tools" in config:
            tools = ToolRegistry()
            for tool_def in config["tools"]:
                if "name" in tool_def and "func" in tool_def:
                    tools.register(tool_def["name"], tool_def["func"])
        
        return cls.create(agent_type, profile, model_config, memory, tools, stream, verbose)
    
    @classmethod
    def register_agent_type(cls, name: str, agent_class: type) -> None:
        """注册新的 Agent 类型"""
        cls.AGENT_TYPES[name] = agent_class

