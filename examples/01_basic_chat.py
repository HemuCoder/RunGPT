"""
示例 1: 基础对话
使用 SimpleAgent 进行简单的对话交互
"""
import os
from dotenv import load_dotenv
from rungpt import SimpleAgent, Thread

# 加载环境变量
load_dotenv()

def main():
    print("=== RunGPT 示例 1: 基础对话 ===\n")
    
    # 创建 SimpleAgent
    # 可以使用 "gpt-4o-mini" 或 "openai:gpt-4o-mini" 格式
    agent = SimpleAgent(
        model="gpt-4o-mini",
        verbose=True,  # 打印详细信息
        temperature=0.7
    )
    
    # 创建对话线程
    thread = Thread()
    
    # 执行单轮对话
    print("\n--- 问题 1 ---")
    response = agent.run("请用一句话介绍什么是人工智能", thread)
    print(f"\n回答: {response}\n")
    
    # 继续对话（带上下文）
    print("\n--- 问题 2 ---")
    thread.add_user("AI 有哪些应用场景？")
    response = agent.run("AI 有哪些应用场景？", thread)
    print(f"\n回答: {response}\n")
    
    # 查看对话历史
    print("\n--- 对话历史 ---")
    context = thread.get_context()
    for i, msg in enumerate(context, 1):
        role = msg['role']
        content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"{i}. [{role}]: {content}")
    
    # 获取执行追踪
    print("\n--- 执行追踪 ---")
    trace = agent.get_trace()
    if trace:
        print(f"Agent: {trace['agent_name']}")
        print(f"状态: {trace['status']}")
        print(f"执行时间: {trace['duration_seconds']:.2f}秒")
        print(f"步骤数: {len(trace['steps'])}")

if __name__ == "__main__":
    main()

