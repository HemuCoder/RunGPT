"""
示例 8: 条件路由 (Routing Workflow)

展示如何使用 Router 根据条件动态选择执行路径。
场景: 根据用户问题的复杂度,选择使用 "简单模型" 还是 "专家模型"。
"""
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rungpt import SimpleAgent
from rungpt.workflow import Pipeline, AgentStep, Router, FunctionStep, WorkflowContext

load_dotenv()

def main():
    print("=== RunGPT Workflow 示例: 条件路由 ===\n")
    
    # 1. 定义 Agent
    # 简单助手 (使用 gpt-3.5-turbo 或更小模型)
    junior = SimpleAgent(
        model="gpt-3.5-turbo",
        system_prompt="你是一个初级助手,回答简洁直接。",
        verbose=True
    )
    
    # 专家助手 (使用 gpt-4)
    expert = SimpleAgent(
        model="gpt-4o",
        system_prompt="你是一个领域专家,回答深入详尽。",
        verbose=True
    )
    
    # 2. 定义分类器 (这里用 FunctionStep 模拟,实际也可以用 Agent)
    def classify_complexity(context: WorkflowContext):
        query = context.query
        # 简单规则: 如果问题包含 "分析"、"设计"、"架构" 等词,视为复杂问题
        complex_keywords = ["分析", "设计", "架构", "原理", "为何"]
        is_complex = any(k in query for k in complex_keywords)
        context.is_complex = is_complex
        print(f"\n[分类器] 问题复杂度判定: {'复杂' if is_complex else '简单'}\n")
        return is_complex

    classifier = FunctionStep(func=classify_complexity, name="Classifier")
    
    # 3. 定义 Workflow
    workflow = Pipeline([
        # 第一步: 分类
        classifier,
        
        # 第二步: 路由
        Router(
            routes=[
                # 路由 1: 复杂问题 -> 专家
                (lambda ctx: ctx.is_complex, 
                 AgentStep(expert, name="Expert", input_key="query", output_key="answer")),
            ],
            # 默认路由: 简单问题 -> 初级助手
            default=AgentStep(junior, name="Junior", input_key="query", output_key="answer")
        )
    ])
    
    # 4. 测试场景
    
    # 场景 A: 简单问题
    print("\n--- 测试场景 A: 简单问题 ---")
    ctx_a = WorkflowContext(query="1+1等于几?")
    workflow.run(ctx_a)
    print(f"回答: {ctx_a.answer}\n")
    
    # 场景 B: 复杂问题
    print("\n--- 测试场景 B: 复杂问题 ---")
    ctx_b = WorkflowContext(query="请分析 Transformer 架构的核心原理")
    workflow.run(ctx_b)
    print(f"回答: {ctx_b.answer[:100]}...\n")

if __name__ == "__main__":
    main()
