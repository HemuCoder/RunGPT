"""
Workflow Patterns
提供常用的编排模式,如 Router (路由)、Parallel (并行) 和 PlanExecute (任务分解)。
"""
from typing import List, Tuple, Callable, Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
from .core import Step, WorkflowContext
from ..agent.agent_base import AgentBase
from ..threads import Thread

# 路由条件类型: 接收 Context 返回 bool
Condition = Callable[[WorkflowContext], bool]
# 路由项: (条件, 步骤)
RouteItem = Tuple[Condition, Step]

class Router(Step):
    """
    条件路由 (Router)
    
    根据 Context 中的状态选择执行路径。
    类似于 if-elif-else 结构。
    """
    def __init__(self, routes: List[RouteItem], default: Optional[Step] = None, name: str = "Router"):
        """
        初始化 Router
        
        Args:
            routes: 路由列表 [(condition, step), ...]
            default: 默认步骤 (如果没有条件匹配)
            name: 步骤名称
        """
        super().__init__(name)
        self.routes = routes
        self.default = default

    def run(self, context: WorkflowContext) -> Any:
        # 遍历路由表
        for condition, step in self.routes:
            if condition(context):
                return step.run(context)
        
        # 没有匹配,执行默认步骤
        if self.default:
            return self.default.run(context)
            
        return None


class Parallel(Step):
    """
    并行执行 (Parallel)
    
    同时执行多个 Step,等待所有 Step 完成。
    """
    def __init__(self, steps: List[Step], max_workers: int = 5, name: str = "Parallel"):
        """
        初始化 Parallel
        
        Args:
            steps: 要并行执行的步骤列表
            max_workers: 最大并发线程数
            name: 步骤名称
        """
        super().__init__(name)
        self.steps = steps
        self.max_workers = max_workers

    def run(self, context: WorkflowContext) -> Dict[str, Any]:
        """
        并行执行所有步骤
        
        Returns:
            Dict[step_name, result]
        """
        results = {}
        
        # 使用线程池并行执行
        # 注意: 这里共享了 context,需要注意线程安全
        # 建议 Parallel 中的 Step 只读取 context,不修改 context,或者修改不同的 key
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_step = {
                executor.submit(step.run, context): step 
                for step in self.steps
            }
            
            for future in as_completed(future_to_step):
                step = future_to_step[future]
                try:
                    result = future.result()
                    results[step.name] = result
                except Exception as e:
                    results[step.name] = f"Error: {str(e)}"
                    # 也可以选择抛出异常终止整个 Parallel
                    # raise e
        
        return results


class Task:
    """子任务"""
    
    def __init__(self, task_id: str, description: str, dependencies: List[str] = None):
        self.id = task_id
        self.description = description
        self.dependencies = dependencies or []
        self.status = "pending"  # pending, running, completed, failed
        self.result: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result
        }


class PlanExecutePattern(Step):
    """
    Plan-Execute 工作流模式
    
    自动完成: 任务规划 → 依赖执行 → 结果总结
    
    用法:
        planner = SimpleAgent(system_prompt="规划助手，输出JSON任务列表", ...)
        executor = ReActAgent(system_prompt="执行助手", tools=..., ...)
        summarizer = SimpleAgent(system_prompt="总结助手", ...)
        
        pattern = PlanExecutePattern(planner, executor, summarizer)
        result = pattern.run({"task": "制定学习计划"})
    """
    
    def __init__(
        self,
        planner: AgentBase,
        executor: AgentBase,
        summarizer: AgentBase,
        max_iterations: int = 20,
        name: str = "PlanExecute"
    ):
        """
        初始化 Plan-Execute 模式
        
        Args:
            planner: 规划 Agent (输出 JSON 任务列表)
            executor: 执行 Agent (执行单个子任务)
            summarizer: 总结 Agent (汇总所有结果)
            max_iterations: 最大执行迭代次数 (防止循环依赖死锁)
            name: 步骤名称
        """
        super().__init__(name)
        self.planner = planner
        self.executor = executor
        self.summarizer = summarizer
        self.max_iterations = max_iterations
    
    def run(self, context: WorkflowContext) -> Any:
        """
        执行 Plan-Execute 循环
        
        Expected context keys:
            - task: 任务描述 (required)
        
        Writes to context:
            - plan: 任务列表
            - task_results: 每个任务的结果
            - result: 最终总结
        """
        task = context.get("task")
        if not task:
            raise ValueError("PlanExecutePattern requires 'task' in context")
        
        # Phase 1: Planning
        tasks = self._planning_phase(task, context)
        context["plan"] = [t.to_dict() for t in tasks]
        
        # Phase 2: Execution
        self._execution_phase(tasks, context)
        context["task_results"] = {t.id: t.result for t in tasks}
        
        # Phase 3: Summarize
        final_result = self._summarize_phase(tasks, context)
        context["result"] = final_result
        
        return final_result
    
    def _planning_phase(self, task: str, context: WorkflowContext) -> List[Task]:
        """规划阶段: 分解任务"""
        planning_prompt = f"""
请将以下任务分解为多个子任务,输出 JSON 格式:

{{
  "tasks": [
    {{"id": "task_1", "description": "任务描述", "dependencies": []}},
    {{"id": "task_2", "description": "任务描述", "dependencies": ["task_1"]}}
  ]
}}

任务: {task}

要求:
- 任务 ID 必须是 task_1, task_2, task_3 格式
- dependencies 是任务 ID 列表
- 确保依赖关系正确,不要循环依赖
"""
        # 使用独立的 Thread
        thread = Thread()
        response = self.planner.run(planning_prompt, thread)
        
        # 解析 JSON
        tasks = self._parse_plan(response)
        return tasks
    
    def _execution_phase(self, tasks: List[Task], context: WorkflowContext):
        """执行阶段: 按依赖顺序执行任务"""
        iteration = 0
        
        while not self._all_completed(tasks) and iteration < self.max_iterations:
            iteration += 1
            ready_tasks = self._get_ready_tasks(tasks)
            
            if not ready_tasks:
                # 没有可执行任务,可能是循环依赖或全部失败
                break
            
            for task in ready_tasks:
                self._execute_task(task, tasks, context)
    
    def _execute_task(self, task: Task, all_tasks: List[Task], context: WorkflowContext):
        """执行单个子任务"""
        task.status = "running"
        
        # 构建执行提示（包含依赖任务的结果）
        prompt_parts = [f"子任务: {task.description}"]
        
        if task.dependencies:
            prompt_parts.append("\n前置任务结果:")
            for dep_id in task.dependencies:
                dep_task = self._get_task_by_id(all_tasks, dep_id)
                if dep_task and dep_task.result:
                    prompt_parts.append(f"- [{dep_id}]: {dep_task.result}")
        
        execution_prompt = "\n".join(prompt_parts)
        
        # 执行任务
        try:
            thread = Thread()
            result = self.executor.run(execution_prompt, thread)
            task.result = result
            task.status = "completed"
        except Exception as e:
            task.result = f"执行失败: {str(e)}"
            task.status = "failed"
    
    def _summarize_phase(self, tasks: List[Task], context: WorkflowContext) -> str:
        """总结阶段: 汇总结果"""
        summary_parts = ["以下是所有子任务的执行结果:\n"]
        
        for task in tasks:
            summary_parts.append(f"[{task.id}] {task.description}")
            summary_parts.append(f"  状态: {task.status}")
            if task.result:
                summary_parts.append(f"  结果: {task.result[:200]}...")
            summary_parts.append("")
        
        summary_parts.append("请基于以上结果,给出最终的总结和答案。")
        
        summary_prompt = "\n".join(summary_parts)
        
        thread = Thread()
        final_result = self.summarizer.run(summary_prompt, thread)
        return final_result
    
    # ========================================
    # 辅助方法
    # ========================================
    
    def _parse_plan(self, response: str) -> List[Task]:
        """解析 JSON 任务列表"""
        # 尝试提取 JSON 代码块
        json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response.strip()
        
        try:
            data = json.loads(json_str)
            task_list = data.get("tasks", [])
            
            tasks = []
            for t_data in task_list:
                task = Task(
                    task_id=t_data["id"],
                    description=t_data["description"],
                    dependencies=t_data.get("dependencies", [])
                )
                tasks.append(task)
            
            return tasks
        except Exception as e:
            raise ValueError(f"无法解析任务计划: {e}\n原始响应: {response}")
    
    def _get_ready_tasks(self, tasks: List[Task]) -> List[Task]:
        """获取可执行的任务（依赖已完成）"""
        ready = []
        for task in tasks:
            if task.status == "pending":
                deps_completed = all(
                    self._get_task_by_id(tasks, dep_id).status == "completed"
                    for dep_id in task.dependencies
                )
                if deps_completed:
                    ready.append(task)
        return ready
    
    def _get_task_by_id(self, tasks: List[Task], task_id: str) -> Optional[Task]:
        """根据 ID 查找任务"""
        for task in tasks:
            if task.id == task_id:
                return task
        return None
    
    def _all_completed(self, tasks: List[Task]) -> bool:
        """检查是否所有任务已完成"""
        return all(t.status in ["completed", "failed"] for t in tasks)

