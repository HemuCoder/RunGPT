"""Context Manager - 上下文管理器（核心入口）"""
from typing import List, Dict, Optional, Any
from .prompt_template import PromptTemplate
from .skill_injector import SkillInjector
from .tool_injector import ToolInjector
from .token_manager import TokenManager


class ContextManager:
    """上下文工程管理器 - 统一生成模型输入的 messages"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化上下文管理器
        
        Args:
            prompts_dir: Prompt 模板目录路径
        """
        self.prompt_template = PromptTemplate(prompts_dir)
        self.tool_injector = ToolInjector()
        self.skill_injector = SkillInjector()
        self.token_manager = TokenManager()
    
    def build_context(
        self,
        thread,
        agent_type: str,
        tools=None,
        skills: Optional[List[str]] = None,
        memory=None,
        system_prompt: Optional[str] = None,
        extra_vars: Optional[Dict[str, Any]] = None,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        构建完整的上下文 messages
        
        Args:
            thread: Thread 对话线程
            agent_type: Agent 类型
            tools: ToolRegistry 工具注册表
            skills: 技能描述列表
            memory: MemoryManager 记忆管理器
            system_prompt: 自定义系统提示词（覆盖默认）
            extra_vars: 额外的模板变量
            max_messages: 最大消息数（用于裁剪）
            
        Returns:
            格式化的 messages 列表
        """
        # 1. 加载模板
        template = self.prompt_template.load(agent_type)
        
        # 2. 准备变量（确保所有模板变量都有默认值）
        variables = extra_vars or {}
        
        # 设置默认 System Prompt 如果未提供
        if not system_prompt:
            system_prompt = "你是一个有帮助的助手。"
        variables['system_prompt'] = system_prompt
        
        # 3. 注入工具描述（无工具时为空字符串）
        variables['tools'] = self.tool_injector.generate_react_format(tools) if tools else ""
        
        # 4. 注入技能（无技能时为空字符串）
        variables['skills'] = self.skill_injector.generate(skills) if skills else ""
        
        # 5. 注入记忆摘要（无记忆时为空字符串）
        variables['memory_summary'] = self._build_memory_summary(memory) if memory else ""
        
        # 6. 渲染 system prompt
        system_prompt = self.prompt_template.render(template, variables)
        
        # 7. 构建 messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # 8. 添加历史消息（去掉 thread 中的旧 system）
        if hasattr(thread, 'get_context'):
            history = [m for m in thread.get_context() if m["role"] != "system"]
            messages.extend(history)
        
        # 9. Token 裁剪
        if max_messages:
            messages = self.token_manager.truncate(messages, max_messages)
        
        return messages
    
    def _build_memory_summary(self, memory) -> str:
        """
        从 Memory 生成摘要文本
        
        Args:
            memory: MemoryManager 实例
            
        Returns:
            记忆摘要文本
        """
        if not memory or not hasattr(memory, 'get_summary'):
            return ""
        
        summary = memory.get_summary()
        if not summary or summary.get('total_memories', 0) == 0:
            return ""
        
        parts = ["[记忆上下文]"]
        
        # 简单版本：列出最近的记忆
        if hasattr(memory, 'memories'):
            recent = sorted(
                memory.memories.values(),
                key=lambda m: m.updated_at,
                reverse=True
            )[:5]  # 最近5条
            
            for mem in recent:
                parts.append(f"  - {mem.key}: {str(mem.value)[:50]}")
        
        return "\n".join(parts) if len(parts) > 1 else ""

