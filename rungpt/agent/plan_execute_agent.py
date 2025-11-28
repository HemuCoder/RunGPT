"""Plan-Execute Agent - 计划-执行推理模式"""
from typing import List, Dict, Any, Optional
from .agent_base import AgentBase
from ..threads import Thread
from ..tools import ToolRegistry
import json
import re


class Task:
    """子任务"""
    
    def __init__(self, task_id: str, description: str, dependencies: List[str] = None):
        self.id = task_id
        self.description = description
        self.dependencies = dependencies or []
        self.status = "pending"
        self.result: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result
        }


class Plan:
    """执行计划"""
    
    def __init__(self, goal: str, tasks: List[Task]):
        self.goal = goal
        self.tasks = tasks
    
    def get_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_ready_tasks(self) -> List[Task]:
        """获取可执行的任务(依赖已完成)"""
        ready = []
        for task in self.tasks:
            if task.status == "pending":
                deps_done = all(
                    self.get_task(dep_id).status == "completed"
                    for dep_id in task.dependencies
                    if self.get_task(dep_id)
                )
                if deps_done:
                    ready.append(task)
        return ready
    
    def is_complete(self) -> bool:
        return all(t.status == "completed" for t in self.tasks)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks]
        }


class PlanExecuteAgent(AgentBase):
    """Plan-Execute Agent - 完整的计划-执行推理循环"""
    
    def __init__(
        self,
        system_prompt: str = "你是一个擅长任务规划和执行的 AI 助手。",
        model: str = "gpt-4o",
        tools: Optional[ToolRegistry] = None,
        allow_replan: bool = False,
        **kwargs
    ):
        """
        初始化 Plan-Execute Agent
        
        Args:
            system_prompt: 系统提示词(默认值会被 agent_plan_execute.txt 模板覆盖)
            model: 模型名称
            tools: 工具注册表(可选,执行阶段可调用工具)
            allow_replan: 是否允许动态调整计划
            **kwargs: 其他参数(name, temperature, max_steps, memory, stream, verbose, debug等)
        """
        # 设置 agent_type 为 plan_execute,让 ContextManager 加载对应模板
        kwargs['name'] = kwargs.get('name', 'PlanExecuteAgent')
        super().__init__(system_prompt, model, **kwargs)
        self.tools = tools
        self.allow_replan = allow_replan
        self.current_plan: Optional[Plan] = None
    
    def _execute(self, task: str, thread: Thread) -> str:
        """
        执行 Plan-Execute 循环
        
        流程:
        1. Plan: 生成任务分解
        2. Execute: 逐个执行子任务
        3. Replan: (可选)根据执行结果调整计划
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"🧠 Plan-Execute Agent - 开始推理")
            print(f"{'='*70}")
            print(f"🎯 任务: {task}\n")
        
        # Phase 1: Planning
        self.current_plan = self._plan_phase(task, thread)
        
        if self.verbose:
            print(f"\n📋 生成了 {len(self.current_plan.tasks)} 个子任务")
            for i, t in enumerate(self.current_plan.tasks, 1):
                deps = f" (依赖: {', '.join(t.dependencies)})" if t.dependencies else ""
                print(f"  {i}. [{t.id}] {t.description}{deps}")
            print()
        
        # Phase 2: Execution
        self._execute_phase(thread)
        
        # Phase 3: Summarize
        summary = self._summarize_phase(thread)
        
        if self.verbose:
            print(f"{'='*70}")
            print(f"✅ Plan-Execute 完成\n")
        
        return summary
    
    def _plan_phase(self, task: str, thread: Thread) -> Plan:
        """规划阶段:生成任务分解"""
        if self.verbose:
            print(f"{'─'*70}")
            print(f"📋 Phase 1: Planning")
            print(f"{'─'*70}")
        
        thread.add_user(f"请为以下任务制定执行计划:\n{task}")
        response = self._call_model(thread)
        thread.add_assistant(response)
        
        plan = self._parse_plan(task, response)
        
        if self.memory:
            self.memory.store("current_plan", plan.to_dict(), category="plan_execute")
        
        self.current_trace.add_step("plan_created", {
            "task_count": len(plan.tasks),
            "plan": plan.to_dict()
        })
        
        return plan
    
    def _execute_phase(self, thread: Thread):
        """执行阶段:逐个执行子任务"""
        if self.verbose:
            print(f"\n{'─'*70}")
            print(f"⚙️  Phase 2: Execution")
            print(f"{'─'*70}\n")
        
        max_iterations = len(self.current_plan.tasks) * 2
        iteration = 0
        
        while not self.current_plan.is_complete() and iteration < max_iterations:
            iteration += 1
            ready_tasks = self.current_plan.get_ready_tasks()
            
            if not ready_tasks:
                break
            
            for task in ready_tasks:
                self._execute_subtask(task, thread)
    
    def _execute_subtask(self, task: Task, thread: Thread):
        """执行单个子任务"""
        if self.verbose:
            print(f"🔄 执行: [{task.id}] {task.description}")
        
        # 构建上下文:包含依赖任务的结果
        context_info = []
        for dep_id in task.dependencies:
            dep_task = self.current_plan.get_task(dep_id)
            if dep_task and dep_task.result:
                context_info.append(f"{dep_id}: {dep_task.result}")
        
        prompt = f"子任务: {task.description}"
        if context_info:
            prompt += f"\n\n前置任务结果:\n" + "\n".join(context_info)
        
        thread.add_user(prompt)
        
        # 如果有工具,可以调用工具
        if self.tools:
            # TODO: 这里可以集成 ReAct 循环,让子任务也能调用工具
            response = self._call_model(thread, max_tokens=500)
        else:
            response = self._call_model(thread, max_tokens=500)
        
        thread.add_assistant(response)
        
        task.status = "completed"
        task.result = response
        
        if self.verbose:
            print(f"  ✅ 完成: {response[:80]}...\n")
        
        if self.memory:
            self.memory.store(f"task_result_{task.id}", response, category="plan_execute")
        
        self.current_trace.add_step("subtask_completed", {
            "task_id": task.id,
            "result": response
        })
    
    def _summarize_phase(self, thread: Thread) -> str:
        """总结阶段:生成最终结果"""
        if self.verbose:
            print(f"{'─'*70}")
            print(f"📊 Phase 3: Summarization")
            print(f"{'─'*70}\n")
        
        completed = [t for t in self.current_plan.tasks if t.status == "completed"]
        
        summary_parts = [
            f"已完成 {len(completed)}/{len(self.current_plan.tasks)} 个子任务:",
            ""
        ]
        
        for task in completed:
            summary_parts.append(f"[{task.id}] {task.description}")
            if task.result:
                summary_parts.append(f"  → {task.result[:100]}...")
            summary_parts.append("")
        
        thread.add_user("请总结以上任务的执行情况,给出最终答案")
        final_summary = self._call_model(thread, max_tokens=500)
        thread.add_assistant(final_summary)
        
        return final_summary
    
    def _parse_plan(self, goal: str, response: str) -> Plan:
        """解析 LLM 输出的计划"""
        json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                task_list = data.get("tasks") or data.get("subtasks") or []
                
                tasks = []
                for t_data in task_list:
                    task_id = str(t_data.get("id", ""))
                    if not task_id.startswith("task_"):
                        task_id = f"task_{task_id}"
                    
                    description = (
                        t_data.get("description") or 
                        t_data.get("name") or 
                        ""
                    )
                    
                    deps = t_data.get("dependencies", [])
                    dependencies = [f"task_{d}" if isinstance(d, int) else str(d) for d in deps]
                    
                    task = Task(task_id, description, dependencies)
                    tasks.append(task)
                
                return Plan(goal, tasks)
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        
        return self._fallback_parse(goal, response)
    
    def _fallback_parse(self, goal: str, response: str) -> Plan:
        """备用解析:从文本中提取任务列表"""
        tasks = []
        lines = response.split('\n')
        task_count = 1
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                desc = re.sub(r'^[\d\-\*\.\)]+\s*', '', line)
                if len(desc) > 5:
                    task = Task(f"task_{task_count}", desc, [])
                    tasks.append(task)
                    task_count += 1
        
        if not tasks:
            tasks = [Task("task_1", goal, [])]
        
        return Plan(goal, tasks)
