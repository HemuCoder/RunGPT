# RunGPT SDK 使用说明书

## 1. 架构总览

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

---

## 2. Models 模块

### 功能
统一封装多平台模型调用，支持流式和非流式输出。

### 核心组件
- `ModelInterface`：抽象基类，定义 `run()` 和 `stream_run()` 接口
- `UnifiedProvider`：默认实现，调用第三方统一 API 平台
- `ModelRegistry`：模型注册表
- `load_model(provider, model_name, **config)`：加载模型实例

### 内置能力
- 自动读取环境变量 `UNIFIED_API_KEY`、`UNIFIED_BASE_URL`
- 自动错误处理（超时、网络异常、响应格式异常）
- 流式输出自动缓冲和解析

---

## 3. Agents 模块

### 核心类型

#### AgentBase（抽象基类）
- 所有 Agent 的父类
- 提供统一的 `run(task, thread)` 接口
- 自动管理执行追踪（`AgentTrace`）
- 内置 `verbose`、`debug`、`stream` 模式

#### SimpleAgent
- **用途**：简单对话、单步工具调用
- **特点**：一次调用即返回结果，可选工具支持
- **适用**：文本生成、单工具查询

#### ReActAgent
- **用途**：多步推理 + 工具调用循环
- **特点**：支持 Thought-Action-Observation 循环
- **适用**：需要多次工具调用、推理链式任务

#### PlannerAgent
- **用途**：任务分解与规划
- **特点**：将复杂任务分解为子任务，输出 JSON 格式计划
- **适用**：复杂任务的前置规划

#### ExecutorAgent
- **用途**：执行规划好的子任务
- **特点**：按依赖顺序执行子任务，支持从 Memory 加载计划
- **适用**：执行 PlannerAgent 输出的计划

### AgentFactory
根据配置动态创建 Agent，支持从字典配置或 Profile 创建。

### 内置能力
- 自动解析模型格式（`provider:model_name` 或 `model_name`）
- 自动保存 Thread 到 Memory
- 自动执行追踪（可通过 `get_trace()` 获取）
- Debug 模式打印完整 Prompt 上下文

---

## 4. Tools 模块

### 功能
工具注册、调用、参数验证，支持自动提取函数签名生成 Schema。

### 核心组件
- `Tool`：工具封装类（name, func, description, parameters, enabled）
- `ToolRegistry`：工具注册表，支持 3 种注册方式（简单注册、装饰器、完整注册）
- `extract_schema`：从函数签名自动提取参数类型、默认值、是否必需
- `ToolValidator`：参数验证器（可选启用）

### 内置能力
- 自动类型映射（Python 类型 → JSON Schema 类型）
- 参数验证（可选）
- 工具启用/禁用、黑名单机制
- 自动错误处理（返回 `Error: ...` 字符串）

---

## 5. Threads 模块

### 功能
管理单次对话的消息历史，支持多角色消息（user/assistant/system/tool）。

### 核心类：Thread
- `add_user(content)`：添加用户消息
- `add_assistant(content)`：添加助手消息
- `add_system(content)`：添加系统消息
- `get_context(max_msgs)`：获取模型上下文（仅 role + content）
- `to_dict()` / `from_dict()`：序列化/反序列化

### 内置能力
- 自动生成线程 ID（`thread_YYYYMMDD_HHMMSS_microseconds`）
- 自动记录消息时间戳
- 支持元数据存储（`set_meta(key, value)`）
- 轻量级、无持久化（持久化由 Memory 管理）

---

## 6. Memory 模块

### 功能
短期任务记忆（跨 Thread），支持记忆分类管理和 Thread 历史存储。

### 核心类：MemoryManager
- `store(key, value, category)`：存储记忆
- `recall(key)`：回忆记忆
- `recall_by_category(category)`：按分类回忆
- `save_thread(thread)`：保存线程
- `load_thread(thread_id)`：加载线程
- `get_summary()`：获取记忆摘要

### 内置能力
- 自动 LRU 淘汰（超过 `max_memories` 时删除最旧记忆）
- 记忆分类（用于结构化存储，如 "planner"、"executor"）
- Thread 历史管理（最多保存 `max_threads` 个）

---

## 7. Context 模块（上下文工程层）

### 功能
统一管理 Prompt 模板、工具描述、技能描述、记忆摘要，自动构建模型输入。

### 核心组件

#### ContextManager（核心入口）
- **功能**：统一生成模型输入的 messages
- **流程**：
  1. 加载 Agent 类型对应的 Prompt 模板
  2. 注入工具描述（ToolInjector）
  3. 注入技能描述（SkillInjector）
  4. 注入记忆摘要（从 Memory）
  5. 渲染模板变量
  6. 合并 Thread 历史消息
  7. Token 裁剪（可选）

#### PromptTemplate
- 加载和渲染 Prompt 模板
- 模板位置：`core/context/prompts/agent_{type}.txt`
- 变量替换：`{system_prompt}`, `{tools}`, `{skills}`, `{memory_summary}`

#### ToolInjector
生成工具描述文本（ReAct 格式），包含工具名称、描述、参数类型、使用示例。

#### SkillInjector
生成技能描述文本，列表形式。

#### TokenManager
简单的消息裁剪（保留 system + 最近 N 条）。

### 内置能力
- 自动去重（移除 Thread 中的旧 system 消息）
- 自动清理多余空行
- 默认值处理（无工具/技能/记忆时自动填充空字符串）
- 模板缓存（避免重复读取文件）

---

## 8. 典型使用流程

### 场景 1：Simple 对话
`SimpleAgent` + `Thread` → 单轮文本生成。

### 场景 2：ReAct 工具调用
`ReActAgent` + `ToolRegistry` + `Thread` → 多步推理 + 工具调用循环。

### 场景 3：Planner + Executor
`PlannerAgent` → 生成计划 → `ExecutorAgent` → 执行计划（需 `MemoryManager` 共享计划）。

### 场景 4：带记忆的多轮对话
`SimpleAgent` + `MemoryManager` → 跨 Thread 保持记忆，自动注入记忆摘要到 Prompt。

---

## 11. 关键设计模式

### 依赖注入
Agent 不直接依赖具体模型，通过 `load_model()` 加载；不直接构建 Prompt，通过 `ContextManager` 统一管理。

### 职责分离
- **Models**：只负责调用 LLM
- **Agents**：只负责执行逻辑（不管 Prompt 细节）
- **Context**：负责组装 Prompt（工具、技能、记忆、模板）
- **Tools**：负责工具定义和调用
- **Memory**：负责跨任务记忆

### 可观测性
所有 Agent 自动生成执行追踪，支持 `verbose` 和 `debug` 模式。

---

## 12. 使用建议

### 选择 Agent 类型
- **单轮对话/文本生成/单次调用工具** → `SimpleAgent`
- **需要多步工具调用** → `ReActAgent`
- **复杂任务分解** → `PlannerAgent` + `ExecutorAgent`

### 性能优化
- 使用 `stream=True` 启用流式输出
- 使用 `max_messages` 限制历史长度
- 使用 `Memory` 存储中间结果

### 调试技巧
- 开启 `verbose=True` 查看执行流程
- 开启 `debug=True` 查看完整 Prompt
- 使用 `agent.get_trace()` 获取执行追踪

---