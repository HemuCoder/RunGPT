"""Agent Base - Agent 抽象基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from ..threads import Thread, MemoryManager
from ..models import ModelInterface
from ..context import ContextManager


class AgentProfile:
    """Agent 配置（内部使用）"""
    
    def __init__(
        self,
        name: str,
        model_name: str = "gpt-4o",
        max_steps: int = 10,
        temperature: float = 0.7,
        **kwargs
    ):
        self.name = name
        self.model_name = model_name
        self.max_steps = max_steps
        self.temperature = temperature
        self.extra = kwargs


class AgentTrace:
    """执行追踪记录"""
    
    def __init__(self, agent_name: str, task: str):
        self.agent_name = agent_name
        self.task = task
        self.steps: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.status = "running"
        self.error: Optional[str] = None
    
    def add_step(self, step_type: str, data: Dict[str, Any]) -> None:
        """添加执行步骤"""
        self.steps.append({
            "type": step_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def finish(self, status: str = "success", error: Optional[str] = None) -> None:
        """结束追踪"""
        self.end_time = datetime.now()
        self.status = status
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "agent_name": self.agent_name,
            "task": self.task,
            "steps": self.steps,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "error": self.error,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None
        }


class AgentBase(ABC):
    """Agent 抽象基类"""
    
    def __init__(
        self,
        system_prompt: str,
        model: Union[str, ModelInterface],
        name: str = "Agent",
        temperature: float = 0.7,
        max_steps: int = 10,
        memory: Optional[MemoryManager] = None,
        stream: bool = False,
        verbose: bool = False,
        debug: bool = False,
        skills: Optional[List[str]] = None,
        **kwargs
    ):
        """
        初始化 Agent
        
        Args:
            system_prompt: 系统提示词
            model: 模型名称（如 "gpt-4o"）或 ModelInterface 实例
            name: Agent 名称
            temperature: 温度参数
            max_steps: 最大步数
            memory: 记忆管理器（可选）
            stream: 是否流式输出
            verbose: 是否详细输出
            debug: 是否调试模式（打印完整 Prompt）
            skills: 技能列表
            **kwargs: 其他扩展参数
        """
        # 构建内部 profile
        self.profile = AgentProfile(
            name=name,
            model_name=model if isinstance(model, str) else "custom",
            temperature=temperature,
            max_steps=max_steps,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 加载模型
        if isinstance(model, str):
            from ..models import load_model
            # 支持 "provider:model_name" 格式，如 "openai:gpt-4o"
            # 如果没有指定 provider，默认使用 "unified"
            if ":" in model:
                provider, model_name = model.split(":", 1)
            else:
                provider = "unified"
                model_name = model
            self.model = load_model(provider, model_name=model_name)
        else:
            self.model = model
        
        self.memory = memory
        self.stream = stream
        self.verbose = verbose
        self.debug = debug
        self.skills = skills
        self.current_trace: Optional[AgentTrace] = None
        
        # 初始化 ContextManager
        self.context_manager = ContextManager()
    
    def run(self, task: str, thread: Optional[Thread] = None) -> str:
        """
        执行任务
        
        Args:
            task: 任务描述
            thread: 对话线程（可选）
            
        Returns:
            执行结果
        """
        thread = thread or Thread()
        self.current_trace = AgentTrace(self.profile.name, task)
        
        try:
            self._pre_run(task, thread)
            result = self._execute(task, thread)
            self._post_run(task, thread, result)
            self.current_trace.finish("success")
            return result
        except Exception as e:
            self.current_trace.finish("error", str(e))
            raise
    
    @abstractmethod
    def _execute(self, task: str, thread: Thread) -> str:
        """
        执行任务主逻辑（子类实现）
        
        Args:
            task: 任务描述
            thread: 对话线程
            
        Returns:
            执行结果
        """
        pass
    
    def _pre_run(self, task: str, thread: Thread) -> None:
        """执行前钩子"""
        self.current_trace.add_step("pre_run", {"task": task})
        self._on_start(task, thread)
    
    def _post_run(self, task: str, thread: Thread, result: str) -> None:
        """执行后钩子"""
        self.current_trace.add_step("post_run", {"result": result[:100]})
        self._on_finish(task, thread, result)
        
        if self.memory:
            self.memory.save_thread(thread)
    
    def _on_start(self, task: str, thread: Thread) -> None:
        """开始回调（子类可重写）"""
        pass
    
    def _on_finish(self, task: str, thread: Thread, result: str) -> None:
        """完成回调（子类可重写）"""
        pass

    def _call_model(self, thread: Thread, **kwargs) -> str:
        """
        调用模型
        
        Args:
            thread: 对话线程
            **kwargs: 模型参数
            
        Returns:
            模型输出
        """
        # 统一使用 ContextManager 构建上下文
        context = self.context_manager.build_context(
            thread=thread,
            agent_type=self.__class__.__name__.replace("Agent", "").lower(),
            tools=getattr(self, 'tools', None),
            skills=self.skills,
            memory=self.memory,
            system_prompt=self.profile.extra.get("system_prompt")
        )
        
        params = {"temperature": self.profile.temperature, **kwargs}
        
        # 🔍 Debug 模式：打印完整 Context
        if self.debug:
            self._print_debug_context(context)
        
        self.current_trace.add_step("model_call", {
            "model": self.profile.model_name,
            "messages_count": len(context),
            "params": params,
            "stream": self.stream
        })
        
        if self.stream:
            response = ""
            for chunk in self.model.stream_run(context, **params):
                print(chunk, end="", flush=True)
                response += chunk
            print()
        else:
            response = self.model.run(context, **params)
        
        self.current_trace.add_step("model_response", {
            "response_length": len(response),
            "preview": response[:200]
        })
        
        return response
    
    def get_trace(self) -> Optional[Dict[str, Any]]:
        """获取执行追踪"""
        return self.current_trace.to_dict() if self.current_trace else None

    def _print_debug_context(self, context: List[Dict[str, str]]) -> None:
        """打印调试上下文信息"""
        print("\n" + "="*30 + " [DEBUG: Prompt Context] " + "="*30)
        print(f"Messages Count: {len(context)}")
        
        for i, msg in enumerate(context):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            print(f"\n[Message {i+1}] ({role.upper()}):")
            print("-" * 20)
            print(content)
            
        print("\n" + "="*80 + "\n")
