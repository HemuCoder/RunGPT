"""
示例 4: 记忆管理
演示如何使用 MemoryManager 进行跨对话记忆管理
"""
import os
from dotenv import load_dotenv
from rungpt import SimpleAgent, Thread, MemoryManager

# 加载环境变量
load_dotenv()

def main():
    print("=== RunGPT 示例 5: 记忆管理 ===\n")
    
    # 创建记忆管理器
    memory = MemoryManager(
        max_memories=100,
        max_threads=10
    )
    
    # 创建带记忆的 Agent
    agent = SimpleAgent(
        model="gpt-4o-mini",
        memory=memory,
        verbose=True
    )
    
    # === 场景 1: 存储和回忆用户信息 ===
    print("--- 场景 1: 用户信息记忆 ---\n")
    
    # 存储用户信息
    memory.store("user_name", "李明", category="user_info")
    memory.store("user_age", "25", category="user_info")
    memory.store("user_interest", "机器学习、Python编程", category="user_info")
    
    print("已存储用户信息到记忆中\n")
    
    # 第一次对话
    thread1 = Thread()
    thread1.add_system("用户名：李明，年龄：25岁，兴趣：机器学习、Python编程")
    response = agent.run("你好，我想学习新技术", thread1)
    print(f"\n回答: {response}\n")
    
    # 保存线程到记忆
    memory.save_thread(thread1)
    print(f"已保存线程 {thread1.id} 到记忆\n")
    
    # === 场景 2: 新对话，利用记忆上下文 ===
    print("\n--- 场景 2: 利用记忆上下文 ---\n")
    
    # 回忆用户信息
    user_name = memory.recall("user_name")
    user_interest = memory.recall("user_interest")
    print(f"从记忆中回忆: 用户名={user_name}, 兴趣={user_interest}\n")
    
    # 新的对话线程
    thread2 = Thread()
    response = agent.run("推荐一些适合我的学习资源", thread2)
    print(f"\n回答: {response}\n")
    
    memory.save_thread(thread2)
    
    # === 场景 3: 按类别管理记忆 ===
    print("\n--- 场景 3: 分类记忆管理 ---\n")
    
    # 存储不同类别的记忆
    memory.store("task1", "学习 Python 基础", category="learning_tasks")
    memory.store("task2", "完成机器学习项目", category="learning_tasks")
    memory.store("book1", "Python 编程从入门到实践", category="resources")
    memory.store("book2", "机器学习实战", category="resources")
    
    # 按类别回忆
    tasks = memory.recall_by_category("learning_tasks")
    resources = memory.recall_by_category("resources")
    
    print("学习任务:")
    for key, value in tasks.items():
        print(f"  - {value}")
    
    print("\n学习资源:")
    for key, value in resources.items():
        print(f"  - {value}")
    
    # === 场景 4: 加载历史线程 ===
    print("\n\n--- 场景 4: 加载历史对话 ---\n")
    
    # 加载之前的线程
    loaded_thread = memory.load_thread(thread1.id)
    if loaded_thread:
        print(f"成功加载线程: {loaded_thread.id}")
        print("\n历史消息:")
        for msg in loaded_thread.messages:
            role = msg['role']
            content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
            print(f"  [{role}]: {content}")
    
    # === 场景 5: 记忆摘要 ===
    print("\n\n--- 场景 5: 记忆摘要 ---\n")
    
    summary = memory.get_summary()
    print(f"总记忆数量: {summary['memory_count']}")
    print(f"保存的线程数: {summary['thread_count']}")
    print(f"记忆类别: {summary['categories']}")
    
    print("\n各类别记忆数量:")
    category_stats = {}
    for category in summary['categories']:
        items = memory.recall_by_category(category)
        category_stats[category] = len(items)
        print(f"  {category}: {len(items)} 条")
    
    # === 场景 6: 清理旧记忆 ===
    print("\n\n--- 场景 6: 记忆清理 ---\n")
    
    # 存储更多记忆，触发 LRU 淘汰
    print(f"当前记忆数: {memory.get_summary()['memory_count']}")
    print(f"最大记忆数: {memory.max_memories}")
    
    # 可以手动清理特定记忆
    # memory.clear_category("resources")
    # print("\n已清理 resources 类别的记忆")
    
    # === 场景 7: 持续对话，Agent 自动使用记忆 ===
    print("\n\n--- 场景 7: 持续对话（自动记忆注入）---\n")
    
    thread3 = Thread()
    
    # Agent 会自动从 memory 中提取相关信息注入到 prompt
    response = agent.run("总结一下我的学习计划", thread3)
    print(f"\n回答: {response}\n")
    
    print("\n提示: Agent 已自动利用记忆中的信息进行回答")

if __name__ == "__main__":
    main()

