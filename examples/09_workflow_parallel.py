"""
示例 9: 并行执行 (Parallel Workflow)

展示如何使用 Parallel 同时执行多个任务,并汇总结果。
场景: 针对一个主题,同时从 "技术"、"商业"、"法律" 三个维度进行分析,最后汇总报告。
"""
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rungpt import SimpleAgent
from rungpt.workflow import Pipeline, AgentStep, Parallel, FunctionStep, WorkflowContext

load_dotenv()

def main():
    print("=== RunGPT Workflow 示例: 并行执行 ===\n")
    
    # 1. 定义 Agent (可以是同一个 Agent 实例,也可以是不同的)
    # 为了演示效果,我们定义三个不同视角的 Agent
    
    tech_agent = SimpleAgent(
        model="gpt-4o-mini",
        system_prompt="你是一个技术专家,关注技术可行性、架构和代码实现。",
        verbose=True
    )
    
    biz_agent = SimpleAgent(
        model="gpt-4o-mini",
        system_prompt="你是一个商业顾问,关注市场规模、商业模式和盈利能力。",
        verbose=True
    )
    
    legal_agent = SimpleAgent(
        model="gpt-4o-mini",
        system_prompt="你是一个法律顾问,关注合规性、知识产权和法律风险。",
        verbose=True
    )
    
    # 2. 定义 Workflow
    workflow = Pipeline([
        # 步骤 1: 并行分析
        Parallel([
            AgentStep(tech_agent, name="TechAnalysis", 
                     input_template="从技术角度分析: {topic}", output_key="tech_report"),
            
            AgentStep(biz_agent, name="BizAnalysis", 
                     input_template="从商业角度分析: {topic}", output_key="biz_report"),
            
            AgentStep(legal_agent, name="LegalAnalysis", 
                     input_template="从法律角度分析: {topic}", output_key="legal_report")
        ], name="MultiPerspectiveAnalysis"),
        
        # 步骤 2: 汇总 (使用 FunctionStep)
        FunctionStep(
            func=lambda ctx: f"""
=== 综合分析报告: {ctx.topic} ===

[技术维度]
{ctx.tech_report}

[商业维度]
{ctx.biz_report}

[法律维度]
{ctx.legal_report}
""",
            name="Aggregator"
        )
    ])
    
    # 3. 执行
    topic = "开发一个能够自动生成代码的 AI 平台"
    print(f"开始并行分析主题: {topic}\n")
    
    ctx = WorkflowContext(topic=topic)
    final_report = workflow.run(ctx)
    
    print("\n" + "="*50)
    print("最终汇总报告")
    print("="*50)
    print(final_report)

if __name__ == "__main__":
    main()
