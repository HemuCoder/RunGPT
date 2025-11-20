"""
示例 4: 任务规划与执行
使用 PlannerAgent 分解任务，ExecutorAgent 执行任务
"""
import os
from dotenv import load_dotenv
from rungpt import PlannerAgent, ExecutorAgent, Thread, MemoryManager, ToolRegistry

# 加载环境变量
load_dotenv()

# 注册一些辅助工具
@ToolRegistry.tool
def search_course(topic: str) -> str:
    """
    搜索课程资源
    
    Args:
        topic: 主题
    
    Returns:
        课程列表
    """
    courses = {
        "Python": "Python 基础教程、Python 高级编程、数据分析实战",
        "机器学习": "机器学习入门、深度学习实战、TensorFlow 教程",
        "Web开发": "HTML/CSS 基础、JavaScript 进阶、Vue.js 实战"
    }
    return courses.get(topic, f"找不到关于 {topic} 的课程")

@ToolRegistry.tool
def create_study_plan(course: str, weeks: int = 4) -> str:
    """
    创建学习计划
    
    Args:
        course: 课程名称
        weeks: 学习周数
    
    Returns:
        学习计划
    """
    return f"{course} 学习计划已创建：共 {weeks} 周，每周 10 小时"

@ToolRegistry.tool
def check_prerequisites(course: str) -> str:
    """
    检查课程前置要求
    
    Args:
        course: 课程名称
    
    Returns:
        前置要求
    """
    return f"{course} 前置要求：基础编程能力、逻辑思维"

def main():
    print("=== RunGPT 示例 4: 任务规划与执行 ===\n")
    
    # 创建记忆管理器（用于在 Planner 和 Executor 之间共享信息）
    memory = MemoryManager(max_memories=50)
    
    # === 阶段 1: 任务规划 ===
    print("--- 阶段 1: 任务规划 ---\n")
    
    planner = PlannerAgent(
        model="gpt-4o-mini",
        memory=memory,
        verbose=True,
        temperature=0.7
    )
    
    # 复杂任务
    complex_task = "我想学习 Python 和机器学习，帮我制定一个完整的学习路线"
    
    thread_plan = Thread()
    plan_result = planner.run(complex_task, thread_plan)
    print(f"\n生成的计划:\n{plan_result}\n")
    
    # === 阶段 2: 任务执行 ===
    print("\n--- 阶段 2: 任务执行 ---\n")
    
    executor = ExecutorAgent(
        model="gpt-4o-mini",
        tools=ToolRegistry,
        memory=memory,
        verbose=True,
        temperature=0.7
    )
    
    # 执行计划
    thread_exec = Thread()
    exec_result = executor.run("执行上述学习计划", thread_exec)
    print(f"\n执行结果:\n{exec_result}\n")
    
    # === 查看记忆 ===
    print("\n--- 记忆状态 ---")
    summary = memory.get_summary()
    print(f"记忆数量: {summary['memory_count']}")
    print(f"线程数量: {summary['thread_count']}")
    
    # 查看计划相关记忆
    planner_memories = memory.recall_by_category("planner")
    if planner_memories:
        print("\n规划器记忆:")
        for key, value in planner_memories.items():
            print(f"  {key}: {str(value)[:100]}...")
    
    # === 另一个示例：项目开发规划 ===
    print("\n\n=== 示例 2: 项目开发规划 ===\n")
    
    project_task = "开发一个简单的待办事项 Web 应用"
    
    print("--- 规划阶段 ---")
    thread_proj = Thread()
    plan = planner.run(project_task, thread_proj)
    print(f"\n项目计划:\n{plan}\n")
    
    # 查看执行追踪
    print("\n--- Planner 执行追踪 ---")
    trace = planner.get_trace()
    if trace:
        print(f"状态: {trace['status']}")
        print(f"执行时间: {trace['duration_seconds']:.2f}秒")

if __name__ == "__main__":
    main()

