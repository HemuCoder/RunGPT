"""
示例 08: Plan-Execute Agent - 统一的计划-执行推理模式

展示如何使用 PlanExecuteAgent 进行任务分解和执行。
这是一个完整的推理循环,类似于 ReAct,但专注于复杂任务的分解。
"""
import os
from dotenv import load_dotenv
from rungpt import PlanExecuteAgent, Thread, MemoryManager

# 加载环境变量
load_dotenv()

def main():
    print("="*70)
    print("Plan-Execute Agent 示例")
    print("="*70)
    print()
    
    # 创建记忆管理器
    memory = MemoryManager()
    
    # 创建 Plan-Execute Agent
    agent = PlanExecuteAgent(
        model="gpt-4o-mini",
        memory=memory,
        verbose=True,  # 显示详细执行过程
        allow_replan=False  # 是否允许动态调整计划
    )
    
    # 创建对话线程
    thread = Thread()
    
    # 示例 1: 学习计划
    print("\n" + "="*70)
    print("示例 1: 制定学习计划")
    print("="*70)
    
    task1 = "制定一份为期一周的 Python 学习计划,包括基础语法、数据结构和实战项目"
    result1 = agent.run(task1, thread)
    
    print("\n最终结果:")
    print("-"*70)
    print(result1)
    print()
    
    # 示例 2: 项目规划
    print("\n" + "="*70)
    print("示例 2: 项目开发规划")
    print("="*70)
    
    thread2 = Thread()
    task2 = "规划一个简单的待办事项 Web 应用的开发流程,包括前端、后端和数据库"
    result2 = agent.run(task2, thread2)
    
    print("\n最终结果:")
    print("-"*70)
    print(result2)
    print()
    
    # 示例 3: 数据分析任务
    print("\n" + "="*70)
    print("示例 3: 数据分析流程")
    print("="*70)
    
    thread3 = Thread()
    task3 = "设计一个用户行为数据分析的完整流程,从数据收集到可视化报告"
    result3 = agent.run(task3, thread3)
    
    print("\n最终结果:")
    print("-"*70)
    print(result3)
    print()
    
    # 对比: 旧方式 vs 新方式
    print("\n" + "="*70)
    print("对比: 旧方式 vs 新方式")
    print("="*70)
    print()
    
    print("❌ 旧方式 (需要手动串联两个 Agent):")
    print("-"*70)
    print("""
from rungpt import PlannerAgent, ExecutorAgent

planner = PlannerAgent(...)
executor = ExecutorAgent(...)

# 第一步: 规划
plan = planner.run("学习 Python")

# 第二步: 执行 (需要手动传递)
result = executor.run(plan, thread)
    """)
    
    print("\n✅ 新方式 (一个 Agent 完成):")
    print("-"*70)
    print("""
from rungpt import PlanExecuteAgent

agent = PlanExecuteAgent(...)

# 一步完成: 自动规划 + 执行
result = agent.run("学习 Python", thread)
    """)
    
    print("\n" + "="*70)
    print("优势:")
    print("="*70)
    print("1. 更简洁: 一个 Agent 替代两个")
    print("2. 更自然: 符合 'Plan-and-Execute' 的推理模式")
    print("3. 更灵活: 可以在执行过程中动态调整计划 (allow_replan=True)")
    print("4. 更一致: 与 ReActAgent 的使用方式保持一致")
    print()

if __name__ == "__main__":
    main()
