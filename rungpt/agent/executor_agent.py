"""Executor Agent - 任务执行 Agent"""
from typing import Optional, Dict, Any
from .agent_base import AgentBase
from .planner_agent import Plan, Task
from ..threads import Thread
import json


class ExecutorAgent(AgentBase):
    """执行 Agent - 执行规划好的任务"""
    
    def __init__(
        self,
        system_prompt: str,
        model: str,
        **kwargs
    ):
        """
        初始化 Executor Agent
        
        Args:
            system_prompt: 系统提示词
            model: 模型名称（如 "gpt-4o"）
            **kwargs: 其他参数（name, temperature, max_steps, memory, stream, verbose, debug等）
        """
        super().__init__(system_prompt, model, **kwargs)
        
        if self.stream and self.verbose:
            print("💬 ExecutorAgent 启用流式输出模式\n")
    
    def _execute(self, task: str, thread: Thread) -> str:
        """
        执行任务或执行计划
        
        Args:
            task: 任务描述或计划（JSON）
            thread: 对话线程
            
        Returns:
            执行结果
        """
        plan = self._load_plan(task)
        
        if plan:
            return self._execute_plan(plan, thread)
        else:
            return self._execute_single_task(task, thread)
    
    def _load_plan(self, task: str) -> Optional[Plan]:
        """加载计划"""
        if self.memory:
            plan_data = self.memory.recall("current_plan")
            if plan_data:
                return self._plan_from_dict(plan_data)
        
        try:
            data = json.loads(task)
            if "tasks" in data:
                return self._plan_from_dict(data)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _plan_from_dict(self, data: Dict[str, Any]) -> Plan:
        """从字典恢复计划"""
        tasks = []
        for t_data in data.get("tasks", []):
            task = Task(
                task_id=t_data["id"],
                description=t_data["description"],
                dependencies=t_data.get("dependencies", [])
            )
            task.status = t_data.get("status", "pending")
            task.result = t_data.get("result")
            tasks.append(task)
        
        return Plan(data.get("goal", ""), tasks)
    
    def _execute_plan(self, plan: Plan, thread: Thread) -> str:
        """执行完整计划"""
        # System Prompt 现在由 AgentBase._call_model -> ContextManager 统一处理
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"⚙️  Executor Agent - 开始执行计划")
            print(f"{'='*70}")
            print(f"📊 总任务数: {len(plan.tasks)}")
            print(f"🎯 目标: {plan.goal}")
            print(f"{'='*70}\n")
        
        results = []
        completed_count = 0
        max_iterations = len(plan.tasks) * 2
        iteration = 0
        
        while completed_count < len(plan.tasks) and iteration < max_iterations:
            iteration += 1
            ready_tasks = plan.get_ready_tasks()
            
            if not ready_tasks:
                break
            
            for task in ready_tasks:
                if self.verbose:
                    print(f"\n{'─'*70}")
                    print(f"🔄 执行子任务: [{task.id}]")
                    print(f"{'─'*70}")
                    print(f"📝 描述: {task.description}")
                    if task.dependencies:
                        print(f"🔗 依赖: {', '.join(task.dependencies)}")
                        for dep_id in task.dependencies:
                            dep_task = plan.get_task(dep_id)
                            if dep_task and dep_task.result:
                                print(f"   └─ {dep_id}: {dep_task.result[:50]}...")
                
                self.current_trace.add_step("execute_subtask", {
                    "task_id": task.id,
                    "description": task.description
                })
                
                if self.verbose:
                    print(f"⏳ 正在执行...\n")
                
                result = self._execute_subtask(task, plan, thread)
                
                task.status = "completed"
                task.result = result
                results.append(f"[{task.id}] {result}")
                completed_count += 1
                
                if self.verbose:
                    print(f"✅ 完成 ({completed_count}/{len(plan.tasks)})")
                    print(f"💬 结果: {result[:100]}...")
                
                if self.memory:
                    self.memory.store(
                        f"task_result_{task.id}",
                        result,
                        category="executor"
                    )
        
        if self.memory:
            self.memory.store("plan_results", results, category="executor")
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"📊 所有子任务执行完成，正在生成总结...")
            print(f"{'='*70}\n")
        
        summary = self._summarize_results(plan, thread)
        
        if self.verbose:
            print(f"{'='*70}")
            print(f"✅ 执行完成")
            print(f"{'='*70}\n")
        
        return summary
    
    def _execute_subtask(self, task: Task, plan: Plan, thread: Thread) -> str:
        """执行单个子任务"""
        context_info = []
        for dep_id in task.dependencies:
            dep_task = plan.get_task(dep_id)
            if dep_task and dep_task.result:
                context_info.append(f"{dep_id}: {dep_task.result}")
        
        prompt = f"子任务：{task.description}"
        if context_info:
            prompt += f"\n\n前置任务结果：\n" + "\n".join(context_info)
        
        thread.add_user(prompt)
        
        response = self._call_model(thread, max_tokens=500)
        
        thread.add_assistant(response)
        
        return response
    
    def _execute_single_task(self, task: str, thread: Thread) -> str:
        """执行单个任务（无计划）"""
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"⚙️  Executor Agent - 单任务模式")
            print(f"{'='*70}")
            print(f"📝 任务: {task}")
            print(f"⏳ 正在执行...\n")
        
        # System Prompt 现在由 AgentBase._call_model -> ContextManager 统一处理
        thread.add_user(task)
        
        response = self._call_model(thread)
        
        thread.add_assistant(response)
        
        if self.verbose:
            print(f"✅ 执行完成")
            print(f"💬 结果: {response[:200]}...")
            print(f"{'='*70}\n")
        
        return response
    
    def _summarize_results(self, plan: Plan, thread: Thread) -> str:
        """总结执行结果"""
        completed = [t for t in plan.tasks if t.status == "completed"]
        pending = [t for t in plan.tasks if t.status == "pending"]
        
        summary_parts = [
            f"计划执行完成 ({len(completed)}/{len(plan.tasks)} 个任务)",
            "",
            "已完成任务："
        ]
        
        for task in completed:
            summary_parts.append(f"- {task.id}: {task.description}")
            if task.result:
                summary_parts.append(f"  结果: {task.result[:100]}...")
        
        if pending:
            summary_parts.append("")
            summary_parts.append("未完成任务：")
            for task in pending:
                summary_parts.append(f"- {task.id}: {task.description}")
        
        thread.add_user("请总结以上任务的执行情况")
        final_summary = self._call_model(thread, max_tokens=300)
        thread.add_assistant(final_summary)
        
        summary_parts.append("")
        summary_parts.append("总结：")
        summary_parts.append(final_summary)
        
        return "\n".join(summary_parts)
    
