# RunGPT SDK

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个强大的 AI Agent 框架，支持多种 Agent 类型、工具调用、记忆管理和上下文工程。

## ✨ 特性

- 🤖 **多种 Agent 类型**：SimpleAgent、ReActAgent、PlannerAgent、ExecutorAgent
- 🔧 **工具系统**：自动 Schema 生成、参数验证、工具注册
- 💾 **记忆管理**：跨任务短期记忆、对话历史管理
- 📝 **上下文工程**：自动 Prompt 组装、工具/技能/记忆注入
- 🌊 **流式支持**：支持流式和非流式输出
- 🔍 **可观测性**：执行追踪、Debug 模式、Verbose 输出
- 🎯 **统一接口**：封装多平台 LLM 调用

## 📦 安装

### 从 GitHub 安装

```bash
pip install git+https://github.com/HemuCoder/rungpt.git
```

### 从源码安装

```bash
git clone https://github.com/HemuCoder/rungpt.git
cd rungpt
pip install -e .
```

### 开发模式安装

```bash
pip install -e ".[dev]"
```

## 🚀 快速开始

### 1. 基础配置

创建 `.env` 文件并配置 API Key：

```env
UNIFIED_API_KEY=your_api_key_here
UNIFIED_BASE_URL=https://api.openai.com/v1
```

### 2. 简单对话（SimpleAgent）

```python
from rungpt import SimpleAgent, Thread

# 创建 Agent
agent = SimpleAgent(
    model="gpt-4o-mini",
    verbose=True
)

# 创建对话线程
thread = Thread()

# 执行任务
response = agent.run("介绍一下人工智能", thread)
print(response)
```

### 3. 工具调用（ReActAgent）

```python
from rungpt import ReActAgent, Thread, ToolRegistry

# 注册工具
@ToolRegistry.tool
def search_weather(city: str) -> str:
    """查询城市天气"""
    return f"{city} 今天晴天，温度 25°C"

# 创建 Agent
agent = ReActAgent(
    model="gpt-4o-mini",
    tools=ToolRegistry,
    verbose=True
)

# 执行任务
thread = Thread()
response = agent.run("查询北京的天气", thread)
print(response)
```

### 4. 任务规划（Planner + Executor）

```python
from rungpt import PlannerAgent, ExecutorAgent, Thread, MemoryManager

# 创建记忆管理器
memory = MemoryManager()

# 创建规划 Agent
planner = PlannerAgent(
    model="gpt-4o-mini",
    memory=memory
)

# 执行规划
thread = Thread()
plan = planner.run("制定一份学习 Python 的计划", thread)

# 创建执行 Agent
executor = ExecutorAgent(
    model="gpt-4o-mini",
    memory=memory
)

# 执行计划
result = executor.run("执行学习计划", thread)
print(result)
```

## 📚 核心模块

### Models - 模型层

统一封装多平台 LLM 调用：

```python
from rungpt import load_model

# 加载模型
model = load_model("unified", model_name="gpt-4o-mini")

# 调用模型
messages = [{"role": "user", "content": "Hello"}]
response = model.run(messages)

# 流式调用
for chunk in model.stream_run(messages):
    print(chunk, end="", flush=True)
```

### Agents - 智能体层

四种预置 Agent：

- **SimpleAgent**：单轮对话、简单工具调用
- **ReActAgent**：多步推理 + 工具调用循环
- **PlannerAgent**：任务分解与规划
- **ExecutorAgent**：执行规划好的任务

### Tools - 工具层

工具注册和调用：

```python
from rungpt import ToolRegistry

# 方式1：装饰器注册
@ToolRegistry.tool
def calculate(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b

# 方式2：手动注册
def search(query: str) -> str:
    """搜索信息"""
    return f"搜索结果：{query}"

ToolRegistry.register(
    name="search",
    func=search,
    description="搜索信息"
)

# 获取所有工具
tools = ToolRegistry.get_all()
```

### Threads - 对话管理

管理对话历史：

```python
from rungpt import Thread

# 创建线程
thread = Thread()

# 添加消息
thread.add_user("你好")
thread.add_assistant("你好！有什么可以帮助你的吗？")

# 获取上下文
context = thread.get_context()

# 序列化
data = thread.to_dict()
```

### Memory - 记忆管理

跨任务记忆：

```python
from rungpt import MemoryManager

# 创建记忆管理器
memory = MemoryManager(max_memories=100)

# 存储记忆
memory.store("user_name", "张三", category="user_info")

# 回忆记忆
name = memory.recall("user_name")

# 按类别回忆
user_info = memory.recall_by_category("user_info")

# 保存线程
memory.save_thread(thread)

# 加载线程
loaded_thread = memory.load_thread(thread.id)
```

### Context - 上下文工程

自动组装 Prompt：

```python
from rungpt import ContextManager

# 创建上下文管理器
context_manager = ContextManager()

# 构建上下文
messages = context_manager.build_context(
    thread=thread,
    agent_type="react",
    tools=ToolRegistry,
    skills=["Python编程", "数据分析"],
    memory=memory,
    system_prompt="你是一个专业的AI助手"
)
```

## 🎯 使用场景

| 场景 | 推荐 Agent | 说明 |
|------|-----------|------|
| 纯文本生成 | SimpleAgent | 单轮对话、简单问答 |
| 工具调用 + 推理 | ReActAgent | 需要多步工具调用的任务 |
| 任务分解 | PlannerAgent | 复杂任务的前置规划 |
| 执行计划 | ExecutorAgent | 执行 PlannerAgent 的输出 |

## 🔧 高级功能

### 流式输出

```python
agent = SimpleAgent(
    model="gpt-4o-mini",
    stream=True  # 启用流式输出
)

response = agent.run("写一篇文章", thread)
```

### Debug 模式

```python
agent = SimpleAgent(
    model="gpt-4o-mini",
    debug=True,   # 打印完整 Prompt
    verbose=True  # 打印执行细节
)

response = agent.run("任务", thread)

# 获取执行追踪
trace = agent.get_trace()
print(trace)
```

### 自定义模型

```python
from rungpt import ModelInterface, ModelRegistry

class CustomModel(ModelInterface):
    def run(self, messages, **kwargs):
        # 自定义实现
        return "response"
    
    def stream_run(self, messages, **kwargs):
        # 流式实现
        yield "chunk"

# 注册自定义模型
ModelRegistry.register("custom", CustomModel)

# 使用自定义模型
model = load_model("custom", model_name="my-model")
```

## 📖 示例

更多示例请查看 [examples](examples/) 目录：

- [基础对话](examples/01_simple_chat.py)
- [工具调用](examples/02_tool_calling.py)
- [ReAct 推理](examples/03_react_agent.py)
- [任务规划](examples/04_planner_executor.py)
- [记忆管理](examples/05_memory_usage.py)

## 🏗️ 架构设计

```
RunGPT SDK
├── Models      # 统一多平台 LLM 调用
├── Agents      # 4 种预置 Agent（Simple/ReAct/Planner/Executor）
├── Tools       # 工具注册、调用、验证
├── Threads     # 对话历史管理
├── Memory      # 跨任务短期记忆
└── Context     # Prompt 模板、工具/技能注入、Token 管理
```

**核心理念**：分层解耦，Agent 通过 ContextManager 统一管理上下文，不直接操作模型和 Prompt。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。

## 📞 联系方式

- GitHub: [https://github.com/HemuCoder/rungpt](https://github.com/HemuCoder/rungpt)
- Issues: [https://github.com/HemuCoder/rungpt/issues](https://github.com/HemuCoder/rungpt/issues)

## 🙏 致谢

感谢所有贡献者的支持！

