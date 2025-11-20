# 贡献指南

感谢您对 RunGPT 的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告 Bug

如果您发现了 Bug，请创建一个 Issue，并包含以下信息：

- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（Python 版本、操作系统等）

### 提交功能请求

如果您有新功能的想法，请创建一个 Issue，描述：

- 功能需求
- 使用场景
- 预期效果

### 提交代码

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个 Pull Request

## 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/HemuCoder/rungpt.git
cd rungpt
```

### 2. 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 3. 配置环境变量

复制 `env.example` 为 `.env` 并填入配置：

```bash
cp env.example .env
```

### 4. 运行测试

```bash
pytest
```

### 5. 代码格式化

```bash
black rungpt/
```

### 6. 代码检查

```bash
flake8 rungpt/
mypy rungpt/
```

## 代码规范

- 遵循 PEP 8 代码风格
- 使用类型注解
- 编写清晰的文档字符串
- 为新功能添加测试
- 保持代码简洁易读

## 提交信息规范

使用清晰的提交信息：

- `feat: 添加新功能`
- `fix: 修复 Bug`
- `docs: 更新文档`
- `style: 代码格式调整`
- `refactor: 重构代码`
- `test: 添加测试`
- `chore: 其他修改`

## 测试

- 为所有新功能编写单元测试
- 确保测试覆盖率不降低
- 运行完整测试套件

## 文档

- 更新 README.md（如果适用）
- 为新功能编写示例代码
- 更新 API 文档

## 行为准则

- 尊重他人
- 保持专业
- 接受建设性批评
- 专注于对项目最有利的事情

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。

## 问题反馈

如有任何问题，请通过以下方式联系：

- 创建 Issue
- 发送邮件至 contact@rungpt.dev

再次感谢您的贡献！

