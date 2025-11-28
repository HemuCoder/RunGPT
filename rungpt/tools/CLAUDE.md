# Tools 模块架构

## 职责

提供工具定义、注册、调用、验证的完整系统。

## 文件组织

```
tools/
├── tool.py        # 工具定义与 Schema 提取
├── registry.py    # 工具注册表
├── result.py      # 标准化返回对象
```

## 核心组件

### Tool (工具定义)

**职责**: 封装工具函数及其元数据

**属性**:
- `name`: 工具名称
- `func`: 工具函数
- `description`: 工具描述
- `parameters`: 参数 Schema (自动提取)
- `enabled`: 是否启用
- `args_schema`: Pydantic 模型 (可选)

**关键方法**:
```python
def call(self, **kwargs) -> ToolResult:
    # 1. Pydantic 验证 (如果有)
    # 2. 调用函数
    # 3. 强制检查返回 ToolResult
    # 4. 捕获异常返回 ToolResult.fail()
```

**最近优化** (2025-11-27):
- ❌ 移除: 自动包装逻辑 (3 层 if-else)
- ✅ 强制: 所有工具必须返回 `ToolResult`
- ✅ 异常处理: 捕获执行错误,返回 `ToolResult.fail()`

### ToolResult (标准化返回)

**职责**: 统一工具返回格式

**设计**:
```python
@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, data: Any) -> "ToolResult":
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        return cls(success=False, error=error)
```

**优势**:
- 明确的成功/失败语义
- LLM 友好的字符串格式
- 易于序列化

### ToolRegistry (工具注册表)

**职责**: 管理工具的注册和调用

**注册方式**:
```python
# 1. 装饰器 (推荐)
@ToolRegistry.tool(description="查询天气")
def get_weather(city: str) -> ToolResult:
    return ToolResult.ok(f"{city}: 晴天")

# 2. 手动注册
ToolRegistry.register("tool_name", func, description="...")

# 3. 完整注册
tool = Tool(name="...", func=..., ...)
ToolRegistry.register_tool(tool)
```

**调用**:
```python
result = ToolRegistry.call("tool_name", param1="value")
# 返回 ToolResult 的字符串表示
```

### Schema 提取

**职责**: 自动从函数签名提取参数 Schema

**支持**:
- 基础类型: `str`, `int`, `float`, `bool`
- 泛型: `Optional[T]`, `List[T]`, `Dict[K, V]`
- Pydantic 模型: v1 和 v2

**示例**:
```python
def search(query: str, limit: Optional[int] = 10) -> ToolResult:
    ...

# 自动提取:
{
    "query": {"type": "string", "required": True},
    "limit": {"type": "integer", "required": False, "default": 10}
}
```

## 设计原则

### 1. 强制统一返回类型

**动机**: 消除特殊情况处理

**旧版本** (坏):
```python
# Tool.call 有 3 层 if-else 判断返回值类型
if not isinstance(result, ToolResult):
    if isinstance(result, dict) and "success" in result:
        if result["success"]:
            return ToolResult.ok(result.get("data"))
        else:
            return ToolResult.fail(result.get("error"))
    return ToolResult.ok(result)
```

**新版本** (好):
```python
# 强制要求,无特殊情况
if not isinstance(result, ToolResult):
    raise TypeError("工具必须返回 ToolResult 对象")
```

### 2. 明确的错误处理

**设计**:
- 参数验证失败 → `ToolResult.fail("参数验证失败: ...")`
- 工具执行异常 → `ToolResult.fail("工具执行失败: ...")`
- 返回类型错误 → `ToolResult.fail("工具执行失败: TypeError...")`

### 3. Pydantic 集成

**优势**:
- 类型安全
- 自动验证
- 丰富的类型支持

**示例**:
```python
from pydantic import BaseModel

class SearchArgs(BaseModel):
    query: str
    limit: int = 10

@ToolRegistry.tool(args_schema=SearchArgs)
def search(**kwargs) -> ToolResult:
    # kwargs 已验证和转换
    return ToolResult.ok(...)
```

## 迁移指南

### 工具函数迁移

**步骤 1**: 导入 ToolResult
```python
from rungpt.tools import ToolResult
```

**步骤 2**: 修改返回类型
```python
# 旧版本
def my_tool(param: str) -> str:
    return "result"

# 新版本
def my_tool(param: str) -> ToolResult:
    return ToolResult.ok("result")
```

**步骤 3**: 错误处理
```python
def my_tool(param: str) -> ToolResult:
    if not param:
        return ToolResult.fail("参数不能为空")
    
    try:
        result = do_something(param)
        return ToolResult.ok(result)
    except Exception as e:
        return ToolResult.fail(f"处理失败: {str(e)}")
```

### 常见模式

**成功返回**:
```python
return ToolResult.ok(data)
return ToolResult.ok({"key": "value"})
return ToolResult.ok([1, 2, 3])
```

**失败返回**:
```python
return ToolResult.fail("错误描述")
return ToolResult.fail(f"未找到: {name}")
```

### 2025-11-28: 参数校验系统优化
- ✅ **删除 validators.py**: 移除 87 行冗余代码,Pydantic 已覆盖所有验证场景
- ✅ **修复类型转换**: `model_dump(mode='python')` 确保强制类型转换 ("123" → 123)
- ✅ **Fail Fast**: Schema 提取失败时抛出明确异常,而非静默返回 `{}`
- ✅ **优化 Union 处理**: 在描述中说明可接受的多种类型,帮助 LLM 理解
- ✅ **架构简化**: 合并 `schema.py` 到 `tool.py`,消除内部耦合,文件数减至 3 个

### 影响
- **代码简洁性**: 删除 87 行未使用代码,文件数从 5 个减少到 3 个
- **类型安全**: 修复 LLM 传字符串导致的运算错误 (如 `"10" / "2"`)
- **可调试性**: 错误在工具注册时暴露,而非运行时静默失败
- **LLM 友好**: Union 类型的描述更清晰,减少参数错误

---

**维护者**: RunGPT Team  
**最后更新**: 2025-11-28

