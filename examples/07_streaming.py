"""
示例 7: 流式输出
演示如何使用流式输出功能
"""
import os
import time
from dotenv import load_dotenv
from rungpt import SimpleAgent, ReActAgent, Thread, ToolRegistry

# 加载环境变量
load_dotenv()

# 注册一个工具
@ToolRegistry.tool
def get_info(topic: str) -> str:
    """
    获取主题信息
    
    Args:
        topic: 主题名称
    
    Returns:
        主题相关信息
    """
    time.sleep(1)  # 模拟延迟
    info = {
        "AI": "人工智能是计算机科学的一个分支，致力于创建智能机器",
        "Python": "Python 是一种高级编程语言，以简洁易读著称",
        "云计算": "云计算是通过互联网提供计算服务的模式"
    }
    return info.get(topic, f"关于 {topic} 的信息")

def main():
    print("=== RunGPT 示例 7: 流式输出 ===\n")
    
    # === 场景 1: SimpleAgent 流式输出 ===
    print("--- 场景 1: SimpleAgent 流式输出 ---\n")
    
    agent_stream = SimpleAgent(
        model="gpt-4o-mini",
        stream=True,  # 启用流式输出
        verbose=False  # 关闭详细输出，避免干扰流式显示
    )
    
    thread1 = Thread()
    
    print("问题: 请写一首关于春天的诗\n")
    print("流式回答: ")
    response = agent_stream.run("请写一首关于春天的诗", thread1)
    print("\n")
    
    # === 场景 2: 对比非流式输出 ===
    print("\n--- 场景 2: 非流式输出（对比）---\n")
    
    agent_normal = SimpleAgent(
        model="gpt-4o-mini",
        stream=False,  # 关闭流式输出
        verbose=False
    )
    
    thread2 = Thread()
    
    print("问题: 请写一首关于夏天的诗\n")
    print("等待完整回答...")
    start_time = time.time()
    response = agent_normal.run("请写一首关于夏天的诗", thread2)
    elapsed = time.time() - start_time
    
    print(f"\n完整回答:\n{response}")
    print(f"\n响应时间: {elapsed:.2f}秒\n")
    
    # === 场景 3: ReActAgent 流式输出 ===
    print("\n--- 场景 3: ReActAgent 流式输出 ---\n")
    
    react_agent = ReActAgent(
        model="gpt-4o-mini",
        tools=ToolRegistry,
        stream=True,
        verbose=True,  # 显示推理过程
        max_steps=3
    )
    
    thread3 = Thread()
    
    print("问题: 介绍一下 Python 的特点\n")
    response = react_agent.run("介绍一下 Python 的特点", thread3)
    print("\n")
    
    # === 场景 4: 长文本流式输出 ===
    print("\n--- 场景 4: 长文本流式输出 ---\n")
    
    agent_long = SimpleAgent(
        model="gpt-4o-mini",
        stream=True,
        verbose=False
    )
    
    thread4 = Thread()
    
    print("问题: 写一篇 500 字的文章，介绍人工智能的发展历程\n")
    print("流式输出（建议用于长文本生成）:\n")
    print("-" * 60)
    response = agent_long.run(
        "写一篇 500 字的文章，介绍人工智能的发展历程",
        thread4
    )
    print("-" * 60)
    print("\n")
    
    # === 场景 5: 控制流式输出的显示 ===
    print("\n--- 场景 5: 自定义流式输出处理 ---\n")
    
    # 直接使用模型的 stream_run（不通过 Agent）
    from rungpt import load_model
    
    model = load_model("unified", model_name="gpt-4o-mini")
    
    messages = [
        {"role": "system", "content": "你是一个专业的助手"},
        {"role": "user", "content": "用三个词描述人工智能"}
    ]
    
    print("自定义处理流式输出:\n")
    full_response = ""
    word_count = 0
    
    for chunk in model.stream_run(messages):
        full_response += chunk
        word_count += len(chunk)
        
        # 自定义显示：每 10 个字符显示一次进度
        if word_count % 10 == 0:
            print(f"[已接收 {word_count} 字符]", end=" ", flush=True)
        
        print(chunk, end="", flush=True)
    
    print(f"\n\n总字符数: {len(full_response)}")
    
    # === 使用建议 ===
    print("\n\n=== 流式输出使用建议 ===\n")
    print("✓ 适合场景:")
    print("  1. 长文本生成（文章、故事、代码等）")
    print("  2. 需要实时反馈的交互场景")
    print("  3. 改善用户体验（减少等待感）")
    print("  4. 聊天机器人对话")
    
    print("\n✗ 不适合场景:")
    print("  1. 需要完整响应才能处理的任务")
    print("  2. 结构化输出（JSON 等）")
    print("  3. 批量处理任务")
    print("  4. 需要精确计时的场景")
    
    print("\n💡 性能对比:")
    print("  - 流式输出: 首字节时间短，用户体验好")
    print("  - 非流式输出: 总时间可能更短，但需要等待完整响应")

if __name__ == "__main__":
    main()

