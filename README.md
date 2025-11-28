# RunGPT SDK

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个强大的 AI Agent 框架，支持多种 Agent 类型、工具调用、记忆管理和上下文工程。

## ✨ 特性

- 🤖 **多种 Agent 类型**：SimpleAgent、ReActAgent
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

两种核心 Agent：

- **SimpleAgent**：单轮对话、简单工具调用
- **ReActAgent**：多步推理 + 工具调用循环

**复杂任务编排**: 使用 Workflow 模式组合多个 Agent

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

| 场景 | 推荐方案 | 说明 |
|------|----------|------|
| 纯文本生成 | SimpleAgent | 单轮对话、简单问答 |
| 工具调用 + 推理 | ReActAgent | 需要多步工具调用的任务 |
| 复杂任务编排 | Workflow | 使用 Pipeline 组合多个 Agent |

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
- [记忆管理](examples/05_memory_usage.py)
- [工作流编排 - 线性流程](examples/10_workflow_linear.py)
- [工作流编排 - Plan-Execute 模式](examples/13_plan_execute_workflow.py)

## 📚 文档

- [框架开发指南](FRAMEWORK_GUIDE.md): 专为 AI 开发者设计的框架集成与使用指南。
- [架构文档](rungpt/CLAUDE.md): 详细的内部架构设计文档。

## 🏗️ 架构设计

```
RunGPT SDK
├── Models      # 统一多平台 LLM 调用
├── Agents      # 2 种核心 Agent（Simple/ReAct）
├── Tools       # 工具注册、调用、验证
├── Threads     # 对话历史管理
├── Memory      # 跨任务短期记忆
├── Context     # Prompt 模板、工具/技能注入、Token 管理
└── Workflow    # 复杂流程编排（Pipeline/Router/Parallel）
```

**核心理念**：
- **Agent 层**: SimpleAgent / ReActAgent（真正的单一职责）
- **Workflow 层**: 复杂任务编排，组合多个 Agent
- 分层解耦，Agent 通过 ContextManager 统一管理上下文

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。

## 📞 联系方式

- GitHub: [https://github.com/HemuCoder/rungpt](https://github.com/HemuCoder/rungpt)
- Issues: [https://github.com/HemuCoder/rungpt/issues](https://github.com/HemuCoder/rungpt/issues)

## 🙏 致谢

感谢所有贡献者的支持！

