# 更新日志

所有重要更改都将记录在此文件中。

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2025-11-20

### 新增

- 🎉 首次发布 RunGPT SDK
- ✨ 支持 4 种 Agent 类型：SimpleAgent、ReActAgent、PlannerAgent、ExecutorAgent
- 🔧 完整的工具系统：注册、调用、验证
- 💾 记忆管理系统：MemoryManager
- 📝 上下文工程：自动 Prompt 组装
- 🌊 流式输出支持
- 🔍 执行追踪和 Debug 模式
- 📚 完整的示例代码和文档

### 核心功能

#### Models（模型层）
- 统一模型接口 `ModelInterface`
- 模型注册表 `ModelRegistry`
- 统一 API 提供者 `UnifiedProvider`
- 支持流式和非流式输出

#### Agents（智能体层）
- `SimpleAgent`：单轮对话和简单任务
- `ReActAgent`：多步推理 + 工具调用
- `PlannerAgent`：任务分解和规划
- `ExecutorAgent`：执行规划任务
- 统一的执行追踪 `AgentTrace`

#### Tools（工具层）
- 工具注册和管理 `ToolRegistry`
- 自动 Schema 生成 `extract_schema`
- 参数验证 `ToolValidator`
- 多种注册方式（装饰器、手动）

#### Threads（对话管理）
- 对话线程 `Thread`
- 消息历史管理
- 序列化和反序列化

#### Memory（记忆管理）
- 记忆管理器 `MemoryManager`
- 分类记忆存储
- LRU 自动淘汰
- Thread 历史管理

#### Context（上下文工程）
- 上下文管理器 `ContextManager`
- Prompt 模板系统 `PromptTemplate`
- 工具注入 `ToolInjector`
- 技能注入 `SkillInjector`
- Token 管理 `TokenManager`

### 文档

- 完整的 README.md
- 7 个详细示例
- API 使用指南
- 贡献指南

### 基础设施

- 标准的 Python 包结构
- pyproject.toml 配置
- setup.py 支持
- .gitignore 和 LICENSE
- MANIFEST.in 包含非代码文件

---

## [未发布]

### 计划功能

- [ ] 添加更多示例
- [ ] 性能优化
- [ ] 更多模型提供者支持
- [ ] 插件系统
- [ ] Web UI
- [ ] 持久化存储支持

---

格式说明：
- `新增` - 新功能
- `修改` - 现有功能的更改
- `弃用` - 即将删除的功能
- `移除` - 已删除的功能
- `修复` - Bug 修复
- `安全` - 安全相关的修复

