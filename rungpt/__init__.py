"""
RunGPT - 强大的 AI Agent 框架

一个支持多种 Agent 类型、工具调用、记忆管理和上下文工程的 Python SDK。
"""

__version__ = "0.1.0"
__author__ = "RunGPT Team"
__license__ = "MIT"

from .models import load_model, ModelInterface, ModelRegistry
from .threads import Thread, MemoryManager
from .context import ContextManager, PromptTemplate, SkillInjector, ToolInjector, TokenManager
from .tools import Tool, ToolRegistry, extract_schema, Validator, ToolValidator, ValidationError
from .agent import (
    AgentBase, AgentProfile, AgentFactory,
    SimpleAgent, ReActAgent, PlanExecuteAgent,
    Plan, Task
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    "__license__",
    # Models
    "load_model", "ModelInterface", "ModelRegistry",
    # Threads
    "Thread", "MemoryManager",
    # Context
    "ContextManager", "PromptTemplate", "SkillInjector", "ToolInjector", "TokenManager",
    # Tools
    "Tool", "ToolRegistry", "extract_schema", "Validator", "ToolValidator", "ValidationError",
    # Agents
    "AgentBase", "AgentProfile", "AgentFactory",
    "SimpleAgent", "ReActAgent", "PlanExecuteAgent",
    "Plan", "Task"
]
