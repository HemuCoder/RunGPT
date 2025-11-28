"""
示例 09: Pydantic 结构化输出

展示如何让 Agent 返回强类型的 Pydantic 对象,而非纯文本。
支持 SimpleAgent, ReActAgent, PlanExecuteAgent 等所有 Agent 类型。
"""
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from rungpt import SimpleAgent, ReActAgent, PlanExecuteAgent, Thread, ToolRegistry
from rungpt.tools.result import ToolResult

# 加载环境变量
load_dotenv()

# 1. 定义 Pydantic 模型
class UserInfo(BaseModel):
    """用户信息模型"""
    name: str = Field(..., description="用户姓名")
    age: int = Field(..., description="用户年龄")
    interests: List[str] = Field(..., description="兴趣爱好列表")
    profession: Optional[str] = Field(None, description="职业")

class WeatherReport(BaseModel):
    """天气报告模型"""
    city: str = Field(..., description="城市名称")
    temperature: float = Field(..., description="温度(摄氏度)")
    condition: str = Field(..., description="天气状况(如晴、雨)")
    advice: str = Field(..., description="出行建议")

def main():
    print("="*70)
    print("Pydantic 结构化输出示例")
    print("="*70)
    print()
    
    # 示例 1: SimpleAgent 提取信息
    print("\n" + "="*70)
    print("示例 1: SimpleAgent 文本提取")
    print("="*70)
    
    simple_agent = SimpleAgent(
        system_prompt="你是一个有帮助的助手。",
        model="gpt-4o-mini"
    )
    thread1 = Thread()
    
    text = "我叫李雷,今年25岁。我是一名软件工程师,平时喜欢打篮球和看科幻电影。"
    task1 = f"从以下文本中提取用户信息:\n{text}"
    
    try:
        # 传入 response_model 参数
        user_info = simple_agent.run(task1, thread1, response_model=UserInfo)
        
        print(f"类型: {type(user_info)}")
        print(f"数据: {user_info}")
        print(f"姓名: {user_info.name}")
        print(f"兴趣: {user_info.interests}")
    except Exception as e:
        print(f"提取失败: {e}")

    # 示例 2: ReActAgent 工具调用 + 结构化输出
    print("\n" + "="*70)
    print("示例 2: ReActAgent 工具调用 + 结构化输出")
    print("="*70)
    
    # 模拟一个天气工具
    def get_weather(city: str) -> ToolResult:
        """查询天气"""
        return ToolResult.ok(f"{city}今天晴朗,气温28度,适合户外活动")
    
    tools = ToolRegistry()
    tools.register("get_weather", get_weather)
    
    react_agent = ReActAgent(
        system_prompt="你是一个有用的助手。",
        model="gpt-4o-mini",
        tools=tools,
        verbose=True
    )
    thread2 = Thread()
    
    task2 = "查询北京的天气,并以结构化报告形式返回"
    
    try:
        # ReActAgent 会先调用工具,最后输出符合 Schema 的 JSON
        report = react_agent.run(task2, thread2, response_model=WeatherReport)
        
        print("\n最终结果:")
        print(f"类型: {type(report)}")
        print(f"城市: {report.city}")
        print(f"温度: {report.temperature}")
        print(f"建议: {report.advice}")
    except Exception as e:
        print(f"执行失败: {e}")

    # 示例 3: PlanExecuteAgent 结构化输出
    print("\n" + "="*70)
    print("示例 3: PlanExecuteAgent 结构化输出")
    print("="*70)
    
    plan_agent = PlanExecuteAgent(
        model="gpt-4o-mini",
        verbose=True
    )
    thread3 = Thread()
    
    task3 = "分析'人工智能发展历史',提取3个关键里程碑,并以结构化形式返回"
    
    class Milestone(BaseModel):
        year: int
        event: str
        significance: str
        
    class HistoryAnalysis(BaseModel):
        topic: str
        milestones: List[Milestone]
        summary: str
    
    try:
        analysis = plan_agent.run(task3, thread3, response_model=HistoryAnalysis)
        
        print("\n最终结果:")
        print(f"主题: {analysis.topic}")
        print("里程碑:")
        for m in analysis.milestones:
            print(f"- {m.year}: {m.event} ({m.significance})")
    except Exception as e:
        print(f"执行失败: {e}")

if __name__ == "__main__":
    main()
