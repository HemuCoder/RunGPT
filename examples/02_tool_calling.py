"""
示例 2: 工具调用
演示如何注册和使用工具
"""
import os
from dotenv import load_dotenv
from rungpt import SimpleAgent, Thread, ToolRegistry

# 加载环境变量
load_dotenv()

# 方式 1: 使用装饰器注册工具
@ToolRegistry.tool
def get_weather(city: str) -> str:
    """
    查询城市天气
    
    Args:
        city: 城市名称
    
    Returns:
        天气信息
    """
    # 模拟天气查询
    weather_data = {
        "北京": "晴天，温度 15-25°C",
        "上海": "多云，温度 18-28°C",
        "深圳": "雨天，温度 22-30°C"
    }
    return weather_data.get(city, f"{city} 的天气信息暂时无法获取")

# 方式 2: 手动注册工具
def calculate_sum(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b

ToolRegistry.register(
    name="calculate_sum",
    func=calculate_sum,
    description="计算两个整数的和"
)

# 方式 3: 注册带默认参数的工具
@ToolRegistry.tool
def search_info(query: str, limit: int = 5) -> str:
    """
    搜索信息
    
    Args:
        query: 搜索关键词
        limit: 返回结果数量，默认 5
    
    Returns:
        搜索结果
    """
    return f"找到关于 '{query}' 的 {limit} 条结果"

def main():
    print("=== RunGPT 示例 2: 工具调用 ===\n")
    
    # 查看已注册的工具
    print("--- 已注册的工具 ---")
    all_tools = ToolRegistry.get_all()
    for tool in all_tools:
        print(f"- {tool.name}: {tool.description}")
    
    # 创建带工具的 Agent
    agent = SimpleAgent(
        model="gpt-4o-mini",
        tools=ToolRegistry,
        verbose=True
    )
    
    # 创建对话线程
    thread = Thread()
    
    # 测试天气查询工具
    print("\n--- 测试 1: 查询天气 ---")
    response = agent.run("帮我查一下北京的天气", thread)
    print(f"\n回答: {response}\n")
    
    # 测试计算工具
    print("\n--- 测试 2: 计算 ---")
    thread_calc = Thread()
    response = agent.run("计算 123 + 456 等于多少", thread_calc)
    print(f"\n回答: {response}\n")
    
    # 测试搜索工具
    print("\n--- 测试 3: 搜索 ---")
    thread_search = Thread()
    response = agent.run("搜索人工智能相关信息，返回 3 条结果", thread_search)
    print(f"\n回答: {response}\n")
    
    # 手动调用工具（不通过 Agent）
    print("\n--- 手动调用工具 ---")
    result = ToolRegistry.call("get_weather", city="上海")
    print(f"上海天气: {result}")

if __name__ == "__main__":
    main()

