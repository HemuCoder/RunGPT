# RunGPT 框架开发指南

本文件旨在为 AI 辅助开发提供上下文，帮助理解 RunGPT 框架的核心能力、设计理念及如何在其他项目中集成和使用 RunGPT。

## 1. 框架概述

RunGPT 是一个轻量级、模块化的 AI Agent 框架，旨在简化 LLM 应用的开发。它提供了从模型调用、Agent 构建、工具管理到记忆系统的全套解决方案。

**核心哲学**：
- **实用主义**：优先解决真实问题，避免过度抽象。
- **显式优于隐式**：关键逻辑（如工具返回值）应显式处理。
- **类型安全**：利用 Python 类型提示和 Pydantic 进行验证。

## 2. 核心组件与使用

### 2.1 Agent 系统

RunGPT 提供了多种预置 Agent，适用于不同场景：

*   **SimpleAgent**: 适用于单轮对话、简单问答或无需工具的纯文本生成。
*   **ReActAgent**: 核心 Agent，支持 "思考-行动-观察" 循环，适用于需要调用工具解决复杂问题的场景。

**复杂任务**: 使用 Workflow 模式组合多个 Agent，实现任务分解、条件路由、并行执行等高级功能。

**使用示例 (ReActAgent)**:

```python
from rungpt import ReActAgent, Thread, ToolRegistry
from rungpt.tools.result import ToolResult

# 定义工具
tools = ToolRegistry()

@tools.tool
def get_weather(city: str) -> ToolResult:
    """查询城市天气"""
    # 注意:必须返回 ToolResult,不能返回 str
    return ToolResult.ok(f"{city}今天晴朗")

# 初始化 Agent (必须提供 system_prompt)
agent = ReActAgent(
    system_prompt="你是一个有用的助手。",
    model="gpt-4o",
    tools=tools,
    verbose=True
)

# 运行任务
thread = Thread()
result = agent.run("帮我查询北京明天的天气", thread)
```

### 2.2 工具系统 (Tool System)

工具是 Agent 与外部世界交互的桥梁。RunGPT 的工具系统强调类型安全和标准化返回。

**关键规则**:
1.  **必须使用 `ToolResult`**: 所有工具函数**必须**返回 `ToolResult` 对象，严禁直接返回字符串或字典。
2.  **类型提示**: 函数参数必须包含类型提示 (Type Hints)。
3.  **文档字符串**: 必须编写清晰的 Docstring，用于生成工具描述。

**定义工具**:

```python
from rungpt.tools import ToolRegistry, ToolResult

@ToolRegistry.tool
def calculate_sum(a: int, b: int) -> ToolResult:
    """
    计算两个整数的和。
    
    Args:
        a: 第一个整数
        b: 第二个整数
    """
    try:
        result = a + b
        return ToolResult.ok(str(result))
    except Exception as e:
        return ToolResult.fail(f"计算出错: {str(e)}")
```

### 2.3 记忆系统 (Memory)

`MemoryManager` 用于管理跨任务的短期记忆和对话历史。

**使用模式**:
- **存储**: `memory.store(key, value, category)`
- **检索**: `memory.recall(key)` 或 `memory.recall_by_category(category)`

### 2.4 工作流系统 (Workflow)

**v2.1 新特性**: 引入 Workflow 层以支持复杂的多步骤任务编排。

**核心概念**:
- **Step**: 所有流程节点的基类
- **Pipeline**: 串行执行一组 Step
- **Router**: 根据条件选择执行路径
- **Parallel**: 并行执行多个 Step
- **PlanExecutePattern**: 任务分解 → 执行 → 总结的完整模式

#### 2.4.1 线性流程 (Pipeline)

```python
from rungpt.workflow import Pipeline, AgentStep
from rungpt import ReActAgent, SimpleAgent

# 1. 定义 Agent
analyst = ReActAgent(...)
writer = SimpleAgent(...)

# 2. 定义 Pipeline
flow = Pipeline([
    AgentStep(analyst, name="analyze", output_key="analysis"),
    AgentStep(writer, name="write", input_key="analysis")
])

# 3. 执行
result = flow.run({"topic": "AI 趋势"})
```

#### 2.4.2 Plan-Execute 模式（推荐）

**适用场景**: 需要自动任务分解和依赖管理的复杂任务

```python
from rungpt import SimpleAgent, ReActAgent
from rungpt.workflow import PlanExecutePattern, WorkflowContext

# 1. 定义 3 个专门的 Agent
planner = SimpleAgent(
    system_prompt="你是任务规划助手，擅长分解复杂任务。",
    model="gpt-4o-mini"
)

executor = ReActAgent(
    system_prompt="你是执行助手，负责完成具体子任务。",
    model="gpt-4o-mini",
    tools=tools  # 可以调用工具
)

summarizer = SimpleAgent(
    system_prompt="你是总结助手，负责汇总结果。",
    model="gpt-4o-mini"
)

# 2. 创建 Pattern
pattern = PlanExecutePattern(
    planner=planner,
    executor=executor,
    summarizer=summarizer
)

# 3. 使用
ctx = WorkflowContext({"task": "制定学习计划"})
result = pattern.run(ctx)

# 4. 获取中间结果
print(ctx.plan)          # 任务列表
print(ctx.task_results)  # 每个任务的结果
print(ctx.result)        # 最终总结
```

**Pattern 自动处理**:
- ✅ JSON 任务列表解析
- ✅ 依赖关系管理
- ✅ 按依赖顺序执行
- ✅ 传递前置任务结果
- ✅ 汇总所有结果

#### 2.4.3 条件路由与并行

```python
from rungpt.workflow import Pipeline, Router, Parallel, AgentStep

flow = Pipeline([
    # 并行搜集信息
    Parallel([
        AgentStep(tech_agent, name="tech"),
        AgentStep(biz_agent, name="biz")
    ]),
    
    # 根据结果路由
    Router(
        routes=[
            (lambda ctx: len(ctx.tech) > 1000, AgentStep(expert_writer)),
        ],
        default=AgentStep(junior_writer)
    )
])
```

### 2.5 模型层 (Models)

统一封装了不同 LLM 提供商（OpenAI, Anthropic 等）的接口。通常通过 `load_model` 使用，但在 Agent 中通常只需指定 `model` 名称字符串，框架会自动处理。

## 3. 项目集成指南

在其他项目中使用 RunGPT 时，建议遵循以下结构：

1.  **依赖安装**: 确保 `rungpt` 已安装 (`pip install rungpt` 或源码安装)。
2.  **环境配置**: 加载 `.env` 文件配置 `UNIFIED_API_KEY` 等。
3.  **工具定义**: 创建专门的 `tools/` 目录，按领域组织工具函数。
4.  **Agent 编排**: 在 `main.py` 或 `core/` 模块中初始化 Agent 和 Thread。

**推荐项目结构**:

```
my_project/
├── .env                # API Keys
├── main.py             # 入口文件
├── tools/              # 工具定义
│   ├── __init__.py
│   ├── search_tools.py
│   └── file_tools.py
└── agents/             # Agent 配置与子类化 (如果需要)
    └── custom_agent.py
```

## 4. 给 AI 开发者的指令 (System Prompt Context)

当你（AI）被要求基于 RunGPT 开发新功能或修复 Bug 时，请遵循：

1.  **检查工具返回**: 确保所有新编写的工具都返回 `ToolResult`。
2.  **优先使用 ReActAgent**: 除非任务极其简单，否则默认选择 `ReActAgent` 以获得工具调用能力。
3.  **保持 Thread 状态**: `Thread` 对象保存了对话上下文，不要在多轮对话中丢失它。
4.  **利用 Pydantic**: 在涉及复杂数据结构时，优先使用 Pydantic 模型定义 Schema。
5.  **参考现有架构**: 遵循 `rungpt/CLAUDE.md` 中描述的架构原则，不要引入不必要的抽象层。


## 5. 常见问题排查

*   **Agent 不调用工具**: 检查工具是否已通过 `@ToolRegistry.tool` 注册，且 Docstring 清晰描述了用途。
*   **参数解析错误**: 检查工具函数的参数类型提示是否正确，尽量使用简单类型 (str, int, bool) 或 Pydantic 模型。
*   **死循环**: 检查 `ReActAgent` 的 `max_steps` 设置，或检查工具是否总是返回相同的失败信息。
*   **工具执行失败**: 确认工具返回 `ToolResult`,不是 `str` 或其他类型。

---
*此文件作为 RunGPT 框架的自我描述，用于指导 AI 理解和使用本框架。*
