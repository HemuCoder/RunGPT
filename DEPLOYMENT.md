# RunGPT SDK 部署指南

本指南介绍如何将 RunGPT SDK 部署到 GitHub 并使其可通过 pip 安装。

## 1. 准备工作

### 1.1 确认项目结构

确保项目结构如下：

```
RunGPT/
├── rungpt/              # 主包
├── examples/            # 示例代码
├── tests/               # 测试代码
├── pyproject.toml       # 项目配置
├── setup.py             # 安装脚本
├── requirements.txt     # 依赖列表
├── README.md            # 项目说明
├── LICENSE              # 许可证
└── .gitignore          # Git 忽略文件
```

### 1.2 验证本地安装

```bash
# 开发模式安装
pip install -e .

# 运行验证脚本
python verify_installation.py

# 运行测试
pytest tests/
```

## 2. 初始化 Git 仓库

### 2.1 初始化仓库（如果还未初始化）

```bash
cd /path/to/RunGPT
git init
```

### 2.2 添加文件

```bash
# 添加所有文件
git add .

# 查看状态
git status

# 提交
git commit -m "Initial commit: RunGPT SDK v0.1.0"
```

### 2.3 查看已添加的文件

```bash
git ls-files
```

## 3. 创建 GitHub 仓库

### 3.1 在 GitHub 上创建仓库

1. 访问 https://github.com/new
2. 仓库名称：`rungpt` 或 `RunGPT`
3. 描述：`一个强大的 AI Agent 框架`
4. 选择 Public（公开）或 Private（私有）
5. **不要**勾选 "Add a README file"（我们已有 README）
6. **不要**选择 .gitignore 或 license（我们已有）
7. 点击 "Create repository"

### 3.2 关联远程仓库

```bash
# 添加远程仓库（替换为您的 GitHub 用户名）
git remote add origin https://github.com/HemuCoder/rungpt.git

# 或使用 SSH
git remote add origin git@github.com:HemuCoder/rungpt.git

# 验证远程仓库
git remote -v
```

### 3.3 推送代码

```bash
# 推送到 main 分支
git branch -M main
git push -u origin main
```

## 4. 配置 GitHub 仓库

### 4.1 更新仓库描述

在 GitHub 仓库页面：
1. 点击右上角的 "Settings"
2. 在 "About" 部分添加：
   - Description: `一个强大的 AI Agent 框架，支持多种 Agent 类型、工具调用、记忆管理和上下文工程`
   - Website: 您的文档网站（如果有）
   - Topics: `python`, `ai`, `agent`, `llm`, `chatbot`, `react`, `planner`

### 4.2 设置 GitHub Pages（可选）

如果要托管文档：
1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: main → /docs
4. Save

### 4.3 启用 Issues 和 Discussions

- Settings → Features
- 勾选 Issues 和 Discussions

## 5. 创建版本标签

### 5.1 创建标签

```bash
# 创建标签
git tag -a v0.1.0 -m "Release version 0.1.0"

# 推送标签
git push origin v0.1.0

# 推送所有标签
git push origin --tags
```

### 5.2 创建 GitHub Release

1. 访问仓库的 Releases 页面
2. 点击 "Create a new release"
3. 选择标签：v0.1.0
4. Release title: `RunGPT v0.1.0`
5. 描述：从 CHANGELOG.md 复制内容
6. 点击 "Publish release"

## 6. 测试安装

### 6.1 从 GitHub 安装

```bash
# 创建新的虚拟环境
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 从 GitHub 安装
pip install git+https://github.com/HemuCoder/rungpt.git

# 验证安装
python -c "import rungpt; print(rungpt.__version__)"

# 运行验证脚本
python verify_installation.py
```

### 6.2 测试特定版本

```bash
# 安装特定标签
pip install git+https://github.com/HemuCoder/rungpt.git@v0.1.0

# 安装特定分支
pip install git+https://github.com/HemuCoder/rungpt.git@dev
```

## 7. 更新 README 和文档

### 7.1 更新所有文档中的 GitHub URL

替换所有文档中的占位符 URL：

```bash
# 查找所有包含占位符的文件
grep -r "HemuCoder" .

# 批量替换（macOS/Linux）
find . -type f -name "*.md" -exec sed -i 's/HemuCoder/your-actual-username/g' {} +
find . -type f -name "*.py" -exec sed -i 's/HemuCoder/your-actual-username/g' {} +

# 批量替换（仅当前目录的 .md 和 .py 文件）
sed -i 's/HemuCoder/your-actual-username/g' *.md
sed -i 's/HemuCoder/your-actual-username/g' **/*.py
```

**需要更新的文件：**
- README.md
- INSTALL.md
- QUICKSTART.md
- PROJECT_STRUCTURE.md
- CONTRIBUTING.md
- pyproject.toml
- setup.py
- examples/*.py

### 7.2 提交更新

```bash
git add .
git commit -m "docs: update GitHub URLs"
git push origin main
```

## 8. 发布到 PyPI（可选）

如果要发布到 PyPI 官方仓库：

### 8.1 注册 PyPI 账号

访问 https://pypi.org/account/register/

### 8.2 安装构建工具

```bash
pip install build twine
```

### 8.3 构建分发包

```bash
python -m build
```

生成文件：
- `dist/rungpt-0.1.0.tar.gz`
- `dist/rungpt-0.1.0-py3-none-any.whl`

### 8.4 上传到 TestPyPI（测试）

```bash
# 上传到 TestPyPI
python -m twine upload --repository testpypi dist/*

# 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ rungpt
```

### 8.5 上传到 PyPI（正式）

```bash
# 上传到 PyPI
python -m twine upload dist/*

# 安装
pip install rungpt
```

## 9. 持续集成（CI/CD）

### 9.1 创建 GitHub Actions 工作流

创建 `.github/workflows/test.yml`：

```yaml
name: Tests

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=rungpt --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 9.2 创建发布工作流

创建 `.github/workflows/release.yml`：

```yaml
name: Release

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: python -m twine upload dist/*
```

## 10. 添加徽章

在 README.md 顶部添加：

```markdown
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/HemuCoder/rungpt.svg)](https://github.com/HemuCoder/rungpt/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/HemuCoder/rungpt.svg)](https://github.com/HemuCoder/rungpt/issues)
[![PyPI](https://img.shields.io/pypi/v/rungpt.svg)](https://pypi.org/project/rungpt/)
[![Downloads](https://pepy.tech/badge/rungpt)](https://pepy.tech/project/rungpt)
```

## 11. 维护和更新

### 11.1 版本更新流程

1. 更新代码
2. 更新 `VERSION` 文件
3. 更新 `rungpt/__init__.py` 中的 `__version__`
4. 更新 `pyproject.toml` 和 `setup.py` 中的版本号
5. 更新 `CHANGELOG.md`
6. 提交并推送
7. 创建新标签
8. 创建 GitHub Release
9. （可选）发布到 PyPI

### 11.2 语义化版本

遵循 [语义化版本](https://semver.org/)：

- **MAJOR** (x.0.0): 不兼容的 API 更改
- **MINOR** (0.x.0): 向后兼容的功能新增
- **PATCH** (0.0.x): 向后兼容的问题修正

## 12. 常见问题

### Q: 如何更新已安装的包？

```bash
pip install --upgrade git+https://github.com/HemuCoder/rungpt.git
```

### Q: 如何指定安装分支？

```bash
pip install git+https://github.com/HemuCoder/rungpt.git@dev
```

### Q: 如何在 requirements.txt 中指定？

```
git+https://github.com/HemuCoder/rungpt.git@v0.1.0
```

### Q: 私有仓库如何安装？

```bash
pip install git+https://YOUR_TOKEN@github.com/HemuCoder/rungpt.git
```

## 13. 检查清单

部署前确认：

- [ ] 所有测试通过
- [ ] 文档完整且准确
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] GitHub URL 已替换
- [ ] .gitignore 正确配置
- [ ] LICENSE 文件存在
- [ ] 示例代码可运行
- [ ] README 徽章已添加
- [ ] 已创建 Git 标签

## 14. 下一步

部署完成后：

1. ⭐ 在 README 中添加使用统计
2. 📚 创建详细的在线文档（如 ReadTheDocs）
3. 🎥 录制使用教程视频
4. 📝 撰写博客文章介绍项目
5. 🐦 在社交媒体宣传
6. 💬 建立社区（Discord/Slack）
7. 🤝 鼓励贡献者参与

---

祝您的 RunGPT SDK 发布成功！🎉

