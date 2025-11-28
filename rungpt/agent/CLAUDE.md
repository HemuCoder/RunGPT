# Agent 模块架构

## 职责

实现不同推理模式的 AI Agent,提供统一的执行接口。

## 文件组织

```
agent/
├── parsers/           # 解析器策略模式 (新增)
│   ├── strategy.py    # 抽象基类和 Action 定义
│   ├── bracket_parser.py  # tool[params] 格式
│   ├── function_parser.py # tool(params) 格式
│   ├── json_parser.py     # JSON 代码块格式
│   ├── robust_parser.py   # 模糊匹配和修复
│   └── parser_manager.py  # 策略编排器
├── agent_base.py      # Agent 抽象基类
├── react_agent.py     # ReAct 推理 Agent (已重构)
├── simple_agent.py    # 简单对话 Agent
├── planner_agent.py   # 规划器 Agent
├── executor_agent.py  # 执行器 Agent
├── agent_factory.py   # Agent 工厂
└── react_parser.py    # ReAct 解析器 (向后兼容层)
```

## 核心设计

### AgentBase (抽象基类)

**职责**: 定义所有 Agent 的通用接口和行为

**关键方法**:
- `run(task, thread)`: 执行任务入口
- `_execute(task, thread)`: 子类实现的核心逻辑
- `_call_model(thread)`: 调用 LLM
- `_pre_run`, `_post_run`: 钩子方法

**设计模式**: 模板方法模式

### ReActAgent (重构版)

**职责**: 实现 Thought-Action-Observation 循环推理

**方法拆分** (消除 164 行巨型方法):
- `_execute(task, thread)`: 主循环 (20 行)
- `_execute_step(step_num, thread)`: 单步执行 (18 行)
- `_handle_action(action, ...)`: 处理工具调用 (17 行)
- `_handle_finish(response, ...)`: 处理完成 (13 行)
- `_handle_error(response, ...)`: 处理格式错误 (15 行)
- `_force_finish(thread)`: 强制结束 (25 行)

**优势**:
- 每个方法职责单一,易于理解
- 易于测试和调试
- 符合"函数不超过 20 行"原则

### 解析器架构 (策略模式)

**问题**: 原 `react_parser.py` 279 行,包含 5 种解析方法,僵化且难以扩展

**解决方案**: 策略模式重构

**架构**:
```
ParserStrategy (抽象基类)
    ├── can_handle(text) -> bool  # 快速判断
    └── parse(text) -> Action     # 解析逻辑

具体策略:
    ├── BracketFormatParser   # tool[params]
    ├── FunctionCallParser    # tool(params)
    ├── JSONActionParser      # JSON 代码块
    └── RobustActionParser    # 模糊匹配(兜底)

ParserManager (编排器)
    └── parse(text) -> Action  # 按优先级尝试策略
```

**优势**:
- 开闭原则: 新增格式只需添加新策略类
- 单一职责: 每个解析器专注一种格式
- 可测试性: 独立测试每个策略
- 代码量: 279 行 → 72 行主文件 + 5 个策略类

### 向后兼容

`react_parser.py` 保留为兼容层:
```python
class ReActParser:
    def __init__(self):
        self._manager = ParserManager()
    
    @staticmethod
    def parse(text):
        parser = ReActParser()
        return parser._parse(text)
```

旧代码无需修改,内部使用新架构。

## 设计原则

### 1. 消除特殊情况
- 解析器: 不再有顺序 if-else,通过策略自然融入
- Agent: 不再有嵌套错误处理,每种情况独立方法

### 2. 简洁性
- 所有方法不超过 25 行
- 不超过 3 层缩进
- 单个文件不超过 300 行

### 3. 可扩展性
- 新增解析格式: 实现 `ParserStrategy`
- 新增 Agent 类型: 继承 `AgentBase`

## 最近优化

### 2025-11-28: 删除结构化输出过度设计 ✨
- ✅ **删除 structured_output.py**: 移除强制 JSON Schema 注入逻辑
- ✅ **删除 response_model 参数**: Agent.run() 只返回字符串，不做假设
- ✅ **删除 format_instruction**: 不教 LLM 怎么输出，让其自然表达
- ✅ **实用主义胜利**: 不对抗假想敌，只解决真实问题

### 设计哲学
> **框架不应该替用户做主。**  
> 如果用户需要结构化输出，他们会在 prompt 中说明，框架只需返回字符串。

### 影响
- **代码简洁性**: 删除 structured_output.py (52 行) + 相关逻辑 (约 30 行)
- **用户体验**: 普通对话不再被强制要求 JSON 格式
- **实用主义**: 代码解决真实问题，不对抗假想敌

### 2025-11-27: 策略模式重构
- ✅ 创建 `parsers/` 子模块
- ✅ 实现 4 个解析策略 + 管理器
- ✅ 重构 `ReActParser` 为兼容层
- ✅ 拆分 `ReActAgent._execute` 为 6 个方法

### 影响
- 代码行数: 279 → 72 (主文件)
- 圈复杂度: 显著降低
- 可维护性: 大幅提升
- 向后兼容: 100%

---

**维护者**: RunGPT Team  
**最后更新**: 2025-11-28
