"""
RunGPT SDK - AI Agent 框架
支持通过 pip install git+https://github.com/... 安装
"""
from setuptools import setup, find_packages
import os

# 读取 README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, encoding="utf-8") as f:
            return f.read()
    return ""

# 读取 requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

setup(
    name="rungpt",
    version="0.1.0",
    description="一个强大的 AI Agent 框架，支持多种 Agent 类型、工具调用、记忆管理和上下文工程",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="RunGPT Team",
    author_email="contact@rungpt.dev",
    url="https://github.com/HemuCoder/rungpt",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="ai agent llm chatbot react planner executor",
    project_urls={
        "Documentation": "https://github.com/HemuCoder/rungpt#readme",
        "Source": "https://github.com/HemuCoder/rungpt",
        "Bug Tracker": "https://github.com/HemuCoder/rungpt/issues",
    },
)

