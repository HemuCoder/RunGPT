"""Planner Agent - 任务规划 Agent"""
from typing import List, Dict, Any, Optional
from .agent_base import AgentBase
from ..threads import Thread
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
        """导出为字典"""
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
        """获取指定任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_ready_tasks(self) -> List[Task]:
        """获取可执行的任务（依赖已完成）"""
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
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks]
        }


class PlannerAgent(AgentBase):
    """规划 Agent - 将复杂任务分解为子任务"""
    
    def __init__(
        self,
        system_prompt: str,
        model: str,
        **kwargs
    ):
        """
        初始化 Planner Agent
        
        Args:
            system_prompt: 系统提示词
            model: 模型名称（如 "gpt-4o"）
            **kwargs: 其他参数（name, temperature, max_steps, memory, stream, verbose, debug等）
        """
        super().__init__(system_prompt, model, **kwargs)
        
        if self.stream and self.verbose:
            print("💬 PlannerAgent 启用流式输出模式\n")
    
    def _execute(self, task: str, thread: Thread) -> str:
        """
        执行任务规划
        
        Args:
            task: 任务描述
            thread: 对话线程
            
        Returns:
            规划结果（JSON 格式）
        """
        # System Prompt 现在由 AgentBase._call_model -> ContextManager 统一处理
        thread.add_user(f"请为以下任务制定执行计划：{task}")
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"📋 Planner Agent - 开始规划")
            print(f"{'='*70}")
            print(f"🎯 任务: {task}")
            print(f"⏳ 正在调用模型生成计划...\n")
        
        response = self._call_model(thread)
        
        if self.verbose:
            print(f"🤖 模型原始输出:")
            print(f"{'-'*70}")
            print(response[:500] + "..." if len(response) > 500 else response)
            print(f"{'-'*70}\n")
        
        thread.add_assistant(response)
        
        plan = self._parse_plan(task, response)
        
        if self.verbose:
            print(f"✅ 解析完成，生成了 {len(plan.tasks)} 个子任务:")
            print(f"{'-'*70}")
            for i, t in enumerate(plan.tasks, 1):
                deps = f" (依赖: {', '.join(t.dependencies)})" if t.dependencies else ""
                print(f"  {i}. [{t.id}] {t.description}{deps}")
            print(f"{'-'*70}\n")
        
        if self.memory:
            self.memory.store("current_plan", plan.to_dict(), category="planner")
        
        self.current_trace.add_step("plan_created", {
            "task_count": len(plan.tasks),
            "plan": plan.to_dict()
        })
        
        if self.verbose:
            print(f"💾 计划已保存到 Memory")
            print(f"{'='*70}\n")
        
        return json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)
    
    def _parse_plan(self, goal: str, response: str) -> Plan:
        """解析规划结果"""
        json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                
                # 兼容多种格式：tasks、subtasks、task_list
                task_list = data.get("tasks") or data.get("subtasks") or data.get("task_list") or []
                
                tasks = []
                for t_data in task_list:
                    # 兼容 id 为数字或字符串
                    task_id = str(t_data.get("id", ""))
                    if not task_id.startswith("task_"):
                        task_id = f"task_{task_id}"
                    
                    # 兼容 description、name、title
                    description = (
                        t_data.get("description") or 
                        t_data.get("name") or 
                        t_data.get("title") or 
                        ""
                    )
                    
                    # 兼容 dependencies 为数字或字符串列表
                    deps = t_data.get("dependencies", [])
                    dependencies = [f"task_{d}" if isinstance(d, int) else str(d) for d in deps]
                    
                    task = Task(
                        task_id=task_id,
                        description=description,
                        dependencies=dependencies
                    )
                    tasks.append(task)
                
                return Plan(goal, tasks)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                if self.verbose:
                    print(f"⚠️  JSON 解析失败: {e}")
        
        return self._fallback_parse(goal, response)
    
    def _fallback_parse(self, goal: str, response: str) -> Plan:
        """备用解析方法（从文本中提取）"""
        tasks = []
        lines = response.split('\n')
        task_count = 1
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                desc = re.sub(r'^[\d\-\*\.\)]+\s*', '', line)
                if len(desc) > 5:
                    task = Task(
                        task_id=f"task_{task_count}",
                        description=desc,
                        dependencies=[]
                    )
                    tasks.append(task)
                    task_count += 1
        
        if not tasks:
            tasks = [Task("task_1", goal, [])]
        
        return Plan(goal, tasks)

