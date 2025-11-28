# RunGPT 示例代码

本目录包含 RunGPT SDK 的各种使用示例。

## 示例列表

1. **01_basic_chat.py** - 基础对话示例
   - 使用 SimpleAgent 进行简单对话
   - 演示基本的 Agent 创建和使用

2. **02_tool_usage.py** - 工具调用示例
   - 注册和使用工具
   - 演示工具参数验证和调用

3. **03_react_agent.py** - ReAct 推理示例
   - 使用 ReActAgent 进行多步推理
   - 演示 Thought-Action-Observation 循环

4. **04_memory_management.py** - 记忆管理示例
   - 跨对话记忆管理
   - Thread 历史保存和加载

5. **05_custom_model.py** - 自定义模型示例
   - 创建自定义模型提供者
   - 注册和使用自定义模型

6. **06_streaming_output.py** - 流式输出示例
   - 启用流式输出
   - 实时显示生成内容

7. **07_workflow_linear.py** - 线性工作流示例
   - 简单的顺序执行流程
   - Step 间的数据传递

8. **08_workflow_routing.py** - 条件路由工作流示例
   - 根据条件选择执行路径
   - Router 模式演示

9. **09_workflow_parallel.py** - 并行工作流示例
   - 并行执行多个 Step
   - 结果汇总

10. **10_workflow_plan_execute.py** - Plan-Execute 模式示例
    - 任务规划与执行
    - 复杂任务分解演示

## 运行前准备

1. 安装 RunGPT SDK：
```bash
pip install git+https://github.com/HemuCoder/rungpt.git
```

2. 配置环境变量（创建 `.env` 文件）：
```env
UNIFIED_API_KEY=your_api_key_here
UNIFIED_BASE_URL=https://api.openai.com/v1
```

3. 运行示例：
```bash
python examples/01_basic_chat.py
```

## 注意事项

- 所有示例都需要配置有效的 API Key
- 示例代码仅供学习参考，生产环境请根据实际需求调整
- 某些示例可能需要额外的依赖包

