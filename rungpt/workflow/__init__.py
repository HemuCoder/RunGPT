"""
RunGPT Workflow Layer
提供基于 Step 的工作流编排能力。

核心理念: Everything is a Step
- 统一抽象: 所有节点都是 Step
- 可组合: Step 可以嵌套 Step
- 显式数据流: 通过 Context 传递数据

基础组件:
- Step: 所有工作流节点的基类
- WorkflowContext: 在 Step 之间传递数据
- Pipeline: 线性执行一组 Step
- AgentStep: 将 Agent 包装为 Step
- FunctionStep: 将函数包装为 Step

编排模式:
- Router: 条件路由
- Parallel: 并行执行
- PlanExecutePattern: 任务分解 → 执行 → 总结

示例:
    # 线性流程
    flow = Pipeline([
        AgentStep(analyst, name="analyze", output_key="analysis"),
        AgentStep(writer, name="write", input_key="analysis")
    ])
    
    # Plan-Execute 模式
    pattern = PlanExecutePattern(planner, executor, summarizer)
    result = pattern.run({"task": "复杂任务"})
"""

from .core import Step, WorkflowContext, Pipeline
from .steps import AgentStep, FunctionStep
from .patterns import Router, Parallel, PlanExecutePattern, Task

__all__ = [
    "Step",
    "WorkflowContext",
    "Pipeline",
    "AgentStep",
    "FunctionStep",
    "Router",
    "Parallel",
    "PlanExecutePattern",
    "Task"
]
