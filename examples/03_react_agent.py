"""
示例 3: ReAct 推理
使用 ReActAgent 进行多步推理和工具调用
"""
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from rungpt import ReActAgent, Thread, ToolRegistry
from rungpt.tools import ToolResult

# 加载环境变量
load_dotenv()

# 实例化工具注册表
registry = ToolRegistry()

# 注册工具
@registry.tool
def search_stock(symbol: str) -> ToolResult:
    """
    查询股票信息
    
    Args:
        symbol: 股票代码
    
    Returns:
        ToolResult 对象
    """
    # 模拟股票数据
    stocks = {
        "AAPL": "苹果公司，当前价格: $175.50，涨幅: +1.2%",
        "TSLA": "特斯拉，当前价格: $242.80，涨幅: -0.5%",
        "GOOGL": "谷歌，当前价格: $138.20，涨幅: +0.8%"
    }
    result = stocks.get(symbol, f"找不到股票代码 {symbol} 的信息")
    return ToolResult.ok(result)

@registry.tool
def calculate_investment(amount: float, price: float) -> ToolResult:
    """
    计算可以购买的股票数量
    
    Args:
        amount: 投资金额
        price: 股票价格
    
    Returns:
        ToolResult 对象
    """
    shares = int(amount / price)
    remaining = amount - (shares * price)
    result = f"可购买 {shares} 股，剩余 ${remaining:.2f}"
    return ToolResult.ok(result)

@registry.tool
def analyze_trend(symbol: str, days: int = 30) -> ToolResult:
    """
    分析股票趋势
    
    Args:
        symbol: 股票代码
        days: 分析天数，默认 30 天
    
    Returns:
        ToolResult 对象
    """
    # 模拟趋势分析
    result = f"{symbol} 在过去 {days} 天呈现上升趋势，建议持有"
    return ToolResult.ok(result)

def main():
    print("=== RunGPT 示例 3: ReAct 推理 ===\n")
    
    # 创建 ReActAgent
    agent = ReActAgent(
        system_prompt="你是一个智能助手，可以使用工具帮助用户解决问题。",
        model="gpt-4o-mini",
        tools=registry,
        max_steps=5,  # 最大推理步数
        verbose=True,
        temperature=0.7
    )
    
    # 场景 1: 单步查询
    print("\n--- 场景 1: 查询股票 ---")
    thread1 = Thread()
    response = agent.run("查询苹果公司（AAPL）的股票信息", thread1)
    print(f"\n最终回答: {response}\n")
    
    # 场景 2: 多步推理
    print("\n--- 场景 2: 投资计算（需要多步推理）---")
    thread2 = Thread()
    task = "我有 $10000，想买特斯拉（TSLA）的股票，帮我查询价格并计算能买多少股"
    response = agent.run(task, thread2)
    print(f"\n最终回答: {response}\n")
    
    # 场景 3: 复杂任务
    print("\n--- 场景 3: 复杂分析任务 ---")
    thread3 = Thread()
    task = "分析谷歌（GOOGL）股票的趋势，并告诉我用 $5000 能买多少股"
    response = agent.run(task, thread3)
    print(f"\n最终回答: {response}\n")
    
    # 查看执行追踪
    print("\n--- 执行追踪 ---")
    trace = agent.get_trace()
    if trace:
        print(f"总步骤数: {len(trace['steps'])}")
        print(f"执行时间: {trace['duration_seconds']:.2f}秒")
        print("\n推理过程:")
        for i, step in enumerate(trace['steps'], 1):
            step_type = step['type']
            if step_type == "thought":
                print(f"{i}. [思考] {step['data'].get('content', '')[:80]}...")
            elif step_type == "action":
                action = step['data']
                print(f"{i}. [行动] {action.get('tool', 'unknown')}({action.get('input', {})})")
            elif step_type == "observation":
                print(f"{i}. [观察] {step['data'].get('result', '')[:80]}...")

if __name__ == "__main__":
    main()

