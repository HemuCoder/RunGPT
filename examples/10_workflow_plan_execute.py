"""
示例 10: Plan-Execute 工作流模式

展示如何使用 PlanExecutePattern 实现任务自动分解和执行。
这是推荐的方式，替代了原有的 PlanExecuteAgent。
"""
import os
import sys
from dotenv import load_dotenv

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rungpt import SimpleAgent, ReActAgent, ToolRegistry
from rungpt.workflow import PlanExecutePattern, WorkflowContext
from rungpt.tools import ToolResult

# 加载环境变量
load_dotenv()


def main():
    print("=== RunGPT Workflow 示例: Plan-Execute 模式 ===\n")
    
    # 1. 定义 3 个专门的 Agent
    
    # 规划 Agent: 负责任务分解
    planner = SimpleAgent(
        system_prompt="你是任务规划助手，擅长将复杂任务分解为清晰的子任务。",
        model="gpt-4o-mini",
        stream=True,
        debug=True,
        verbose=True
    )
    
    # 执行 Agent: 负责执行单个子任务（可以调用工具）
    tools = ToolRegistry()
    
    @tools.tool
    def search_info(query: str) -> ToolResult:
        """搜索信息"""
        # 模拟搜索
        mock_results = {
            "Python 基础": "Python 是一门高级编程语言，适合初学者...",
            "数据结构": "常用数据结构包括列表、字典、集合...",
            "项目实战": "推荐项目：Web 爬虫、数据分析、API 开发..."
        }
        for key, value in mock_results.items():
            if key in query:
                return ToolResult.ok(value)
        return ToolResult.ok(f"找到关于 {query} 的相关信息")
    
    executor = ReActAgent(
        system_prompt="你是执行助手，负责完成具体的子任务。如果需要信息，可以使用工具。",
        model="gpt-4o-mini",
        tools=tools,
        verbose=True,
        max_steps=3,
        stream=True,
        debug=True
    )
    
    # 总结 Agent: 负责汇总结果
    summarizer = SimpleAgent(
        system_prompt="你是总结助手，负责将所有子任务的结果整合成完整的答案。",
        model="gpt-4o-mini",
        verbose=True,
        stream=True,
        debug=True
    )
    
    # 2. 创建 Plan-Execute 模式
    plan_execute = PlanExecutePattern(
        planner=planner,
        executor=executor,
        summarizer=summarizer,
        name="LearningPlanFlow"
    )
    
    # 3. 执行任务
    task = "制定一份为期一周的 Python 学习计划，包括基础语法、数据结构和实战项目"
    
    print(f"任务: {task}\n")
    print("="*70 + "\n")
    
    # 创建上下文
    ctx = WorkflowContext({"task": task})
    
    # 运行工作流
    result = plan_execute.run(ctx)
    
    # 4. 查看结果
    print("\n" + "="*70)
    print("执行完成！")
    print("="*70)
    
    print("\n📋 生成的计划:")
    for task_dict in ctx.plan:
        deps = f" (依赖: {', '.join(task_dict['dependencies'])})" if task_dict['dependencies'] else ""
        print(f"  - [{task_dict['id']}] {task_dict['description']}{deps}")
    
    print("\n📊 执行结果:")
    for task_id, task_result in ctx.task_results.items():
        print(f"  - [{task_id}]: {task_result[:80]}...")
    
    print("\n✅ 最终答案:")
    print("-"*70)
    print(result)


if __name__ == "__main__":
    main()

