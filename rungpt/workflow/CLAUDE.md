# Workflow 模块架构

## 职责

提供基于 Step 的工作流编排能力，支持线性、条件路由、并行、Plan-Execute 等多种编排模式。

## 文件组织

```
workflow/
├── core.py      # 核心抽象 (Step, Context, Pipeline)
├── steps.py     # 基础 Step 实现 (AgentStep, FunctionStep)
└── patterns.py  # 编排模式 (Router, Parallel, PlanExecutePattern)
```

## 核心设计

### 设计理念: Everything is a Step

```
Step (ABC)
├─ Pipeline: 线性执行一组 Step
├─ Router: 条件路由
├─ Parallel: 并行执行
├─ AgentStep: 包装 Agent 为 Step
├─ FunctionStep: 包装函数为 Step
└─ PlanExecutePattern: Plan-Execute 模式
```

**优势**:
- 统一抽象: 所有节点都是 Step
- 可组合: Step 可以嵌套 Step
- 可扩展: 用户可以自定义 Step

---

## 核心组件

### 1. WorkflowContext

**职责**: 在 Step 之间传递数据

```python
class WorkflowContext(dict):
    """
    工作流上下文
    
    支持属性访问和字典访问:
    - context.key 或 context['key']
    """
```

**特性**:
- 继承 dict，支持所有字典操作
- 支持属性访问: `context.result`
- 在 Step 之间传递，像河流一样流动

---

### 2. Step (抽象基类)

**职责**: 所有工作流节点的基类

```python
class Step(ABC):
    @abstractmethod
    def run(self, context: WorkflowContext) -> Any:
        pass
```

**设计模式**: 策略模式
- 不同 Step 实现不同策略
- 通过 run() 统一接口执行

---

### 3. Pipeline

**职责**: 线性执行一组 Step

```python
pipeline = Pipeline([
    step1,
    step2,
    step3
])

result = pipeline.run(context)
```

**特性**:
- Pipeline 本身也是 Step（组合优于继承）
- 可以嵌套: Pipeline([step1, Pipeline([step2, step3])])
- 顺序执行，前一步的输出可作为后一步的输入

---

### 4. AgentStep

**职责**: 将 Agent 包装为 Step

```python
step = AgentStep(
    agent=agent,
    name="analyze",
    input_key="topic",           # 从 Context 读取
    output_key="analysis",       # 写入 Context
    input_template="分析: {topic}"  # 可选的模板
)
```

**特性**:
- 显式数据流: input_key/output_key 明确数据流向
- 支持模板: input_template 可以组合多个 context 字段
- 独立 Thread: 每个 AgentStep 使用独立 Thread

---

### 5. Router

**职责**: 条件路由

```python
router = Router(
    routes=[
        (lambda ctx: ctx.score > 80, high_quality_step),
        (lambda ctx: ctx.score > 60, medium_quality_step),
    ],
    default=low_quality_step
)
```

**特性**:
- 按顺序检查条件
- 匹配第一个满足的路由
- 支持 default 路由

---

### 6. Parallel

**职责**: 并行执行多个 Step

```python
parallel = Parallel([
    step1,
    step2,
    step3
], max_workers=5)

results = parallel.run(context)
# 返回 {"step1": result1, "step2": result2, "step3": result3}
```

**特性**:
- 使用 ThreadPoolExecutor 并行执行
- 等待所有 Step 完成
- 返回字典，key 为 step.name

**注意**: 并行 Step 应避免修改 context 的相同 key

---

### 7. PlanExecutePattern

**职责**: 任务分解 → 执行 → 总结的完整模式

```python
pattern = PlanExecutePattern(
    planner=planner_agent,      # 规划 Agent
    executor=executor_agent,    # 执行 Agent
    summarizer=summarizer_agent # 总结 Agent
)

result = pattern.run({"task": "复杂任务"})
```

**自动处理**:
1. **Planning**: 调用 planner 生成 JSON 任务列表
2. **Execution**: 按依赖关系执行任务
3. **Summarization**: 汇总所有结果

**核心优势**:
- 自动解析 JSON 任务列表
- 自动管理依赖关系 (dependencies)
- 自动传递前置任务结果
- 防止循环依赖死锁

---

## 设计原则

### 1. Everything is a Step

**理念**: 统一抽象，可组合

```python
# Pipeline 是 Step
pipeline = Pipeline([...])

# PlanExecutePattern 也是 Step
plan_execute = PlanExecutePattern(...)

# 可以组合
flow = Pipeline([
    plan_execute,
    AgentStep(reviewer)
])
```

### 2. 显式数据流

**理念**: 通过 input_key/output_key 显式声明数据流向

```python
AgentStep(
    agent=analyst,
    input_key="topic",      # 从哪里读
    output_key="analysis"   # 写到哪里
)
```

**优势**:
- 清晰的数据流向
- 易于调试
- 避免隐式依赖

### 3. 无侵入性

**理念**: 现有 Agent 无需修改即可接入 Workflow

```python
# 定义普通 Agent
agent = ReActAgent(...)

# 直接包装为 Step
step = AgentStep(agent, ...)

# 无需修改 Agent 代码
```

### 4. 组合优于继承

**理念**: 通过组合 Step 构建复杂流程

```python
# ✅ 好: 组合 3 个 Agent
pattern = PlanExecutePattern(planner, executor, summarizer)

# ❌ 坏: 强行塞到一个 Agent 类里
class PlanExecuteAgent:  # 伪装成单 Agent
    def __init__(self):
        self.planner = ...
        self.executor = ...
```

---

## 最近优化

### 2025-11-28: 新增 PlanExecutePattern ✨

**动机**: 
- 删除了 PlanExecuteAgent（伪装成单 Agent）
- 用户需要"任务分解 → 执行 → 总结"的通用模式
- 应该作为 Workflow Pattern，而非 Agent

**设计**:
- 继承 Step，可组合
- 用户自定义 3 个 Agent（planner/executor/summarizer）
- Pattern 管理格式要求和依赖关系

**优势**:
- 清晰定位: 是 Workflow Pattern，不是 Agent
- 灵活性高: 用户完全控制 3 个 Agent
- 职责分离: System Prompt 定义角色，User Prompt 定义格式
- 可嵌套: 可以作为 Pipeline 的一部分

---

## 使用场景

| 场景 | 推荐模式 | 说明 |
|------|---------|------|
| 线性流程 | Pipeline | 分析 → 写作 → 审核 |
| 条件分支 | Router | 根据结果选择不同处理路径 |
| 并行处理 | Parallel | 同时搜集多个数据源 |
| 任务分解 | PlanExecutePattern | 复杂任务自动分解和执行 |
| 复杂编排 | 组合使用 | Pipeline + Router + Parallel |

---

## 示例代码

### 线性流程
```python
flow = Pipeline([
    AgentStep(analyst, name="analyze", output_key="analysis"),
    AgentStep(writer, name="write", input_key="analysis")
])
```

### Plan-Execute
```python
pattern = PlanExecutePattern(planner, executor, summarizer)
result = pattern.run({"task": "制定学习计划"})
```

### 条件路由 + 并行
```python
flow = Pipeline([
    Parallel([step1, step2]),
    Router([(condition, step3)], default=step4)
])
```

---

**维护者**: RunGPT Team  
**最后更新**: 2025-11-28

