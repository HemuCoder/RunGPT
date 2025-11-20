"""
示例 3: ReAct 推理
使用 ReActAgent 进行多步推理和工具调用
"""
import os
from dotenv import load_dotenv
from rungpt import ReActAgent, Thread, ToolRegistry

# 加载环境变量
load_dotenv()

# 注册工具
@ToolRegistry.tool
def search_stock(symbol: str) -> str:
    """
    查询股票信息
    
    Args:
        symbol: 股票代码
    
    Returns:
        股票信息
    """
    # 模拟股票数据
    stocks = {
        "AAPL": "苹果公司，当前价格: $175.50，涨幅: +1.2%",
        "TSLA": "特斯拉，当前价格: $242.80，涨幅: -0.5%",
        "GOOGL": "谷歌，当前价格: $138.20，涨幅: +0.8%"
    }
    return stocks.get(symbol, f"找不到股票代码 {symbol} 的信息")

@ToolRegistry.tool
def calculate_investment(amount: float, price: float) -> str:
    """
    计算可以购买的股票数量
    
    Args:
        amount: 投资金额
        price: 股票价格
    
    Returns:
        可购买数量
    """
    shares = int(amount / price)
    remaining = amount - (shares * price)
    return f"可购买 {shares} 股，剩余 ${remaining:.2f}"

@ToolRegistry.tool
def analyze_trend(symbol: str, days: int = 30) -> str:
    """
    分析股票趋势
    
    Args:
        symbol: 股票代码
        days: 分析天数，默认 30 天
    
    Returns:
        趋势分析
    """
    # 模拟趋势分析
    return f"{symbol} 在过去 {days} 天呈现上升趋势，建议持有"

def main():
    print("=== RunGPT 示例 3: ReAct 推理 ===\n")
    
    # 创建 ReActAgent
    agent = ReActAgent(
        model="gpt-4o-mini",
        tools=ToolRegistry,
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

