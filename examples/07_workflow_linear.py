"""
示例 7: 线性工作流 (Linear Workflow)

展示如何使用 Pipeline 串联多个 Agent,实现 "分析 -> 写作" 的自动化流程。
"""
import os
import sys
from dotenv import load_dotenv

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rungpt import SimpleAgent, ReActAgent
from rungpt.workflow import Pipeline, AgentStep, WorkflowContext

# 加载环境变量
load_dotenv()

def main():
    print("=== RunGPT Workflow 示例: 线性流程 ===\n")
    
    # 1. 定义 Agent
    # 分析师: 负责分析问题
    analyst = ReActAgent(
        model="gpt-4o-mini",
        system_prompt="你是一个专业的商业分析师,负责深入分析用户提出的问题。",
        verbose=True,
        debug=True
    )
    
    # 作家: 负责基于分析结果写文章
    writer = SimpleAgent(
        model="gpt-4o-mini",
        system_prompt="你是一个优秀的专栏作家,负责将枯燥的分析报告转化为通俗易懂的文章。",
        verbose=True
    )
    
    # 2. 定义 Workflow
    pipeline = Pipeline([
        # 步骤 1: 分析
        AgentStep(
            agent=analyst,
            name="Analyst",
            input_key="topic",           # 从 Context 读取 'topic'
            output_key="analysis",       # 结果写入 'analysis'
            input_template="请分析以下主题的商业前景: {topic}"
        ),
        
        # 步骤 2: 写作
        AgentStep(
            agent=writer,
            name="Writer",
            input_key="analysis",        # 从 Context 读取 'analysis' (上一步的输出)
            output_key="article",        # 结果写入 'article'
            input_template="根据以下分析报告,写一篇简短的公众号文章:\n\n{analysis}"
        )
    ])
    
    # 3. 执行 Workflow
    topic = "AI Agent 在企业中的应用"
    print(f"开始执行工作流, 主题: {topic}\n")
    
    # 初始 Context
    initial_context = {"topic": topic}
    
    # 运行
    pipeline.run(initial_context)
    
    # 4. 获取结果
    # 注意: pipeline.run() 返回最后一步的结果,但我们也可以从 context 中获取中间结果
    # 由于 context 在 run 过程中被修改,我们需要传入一个 Context 对象才能在外部访问
    
    # 重新运行一次演示 Context 访问
    ctx = WorkflowContext(initial_context)
    pipeline.run(ctx)
    
    print("\n" + "="*50)
    print("最终产出文章:")
    print("="*50)
    print(ctx.article)
    
    print("\n" + "="*50)
    print("中间分析结果:")
    print("="*50)
    print(ctx.analysis[:200] + "...") # 只打印前200字

if __name__ == "__main__":
    main()
