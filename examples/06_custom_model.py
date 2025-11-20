"""
示例 6: 自定义模型
演示如何创建和使用自定义模型提供者
"""
import os
from typing import List, Dict
from dotenv import load_dotenv
from rungpt import ModelInterface, ModelRegistry, load_model, SimpleAgent, Thread

# 加载环境变量
load_dotenv()

class MockModel(ModelInterface):
    """
    模拟模型（用于测试，不调用真实 API）
    """
    
    def __init__(self, model_name: str, **config):
        super().__init__(model_name, **config)
        self.response_template = config.get(
            "response_template", 
            "这是来自 MockModel 的回复：{user_message}"
        )
    
    def run(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """非流式执行"""
        # 获取最后一条用户消息
        user_msg = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_msg = msg.get('content', '')
                break
        
        # 生成模拟回复
        response = self.response_template.format(user_message=user_msg)
        
        # 可以在这里添加自定义逻辑
        if "天气" in user_msg:
            response = "今天天气晴朗，温度适宜。"
        elif "你好" in user_msg:
            response = "你好！我是 MockModel，很高兴为您服务。"
        
        return response
    
    def stream_run(self, messages: List[Dict[str, str]], **kwargs):
        """流式执行"""
        response = self.run(messages, **kwargs)
        
        # 模拟流式输出（逐字返回）
        for char in response:
            yield char

class EchoModel(ModelInterface):
    """
    回声模型（返回用户输入的内容）
    """
    
    def run(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """非流式执行"""
        user_msg = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_msg = msg.get('content', '')
                break
        
        return f"Echo: {user_msg}"
    
    def stream_run(self, messages: List[Dict[str, str]], **kwargs):
        """流式执行"""
        response = self.run(messages, **kwargs)
        for word in response.split():
            yield word + " "

def main():
    print("=== RunGPT 示例 6: 自定义模型 ===\n")
    
    # === 方式 1: 直接使用自定义模型类 ===
    print("--- 方式 1: 直接使用自定义模型 ---\n")
    
    mock_model = MockModel(
        model_name="mock-v1",
        response_template="MockModel 回复：{user_message}"
    )
    
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ]
    
    response = mock_model.run(messages)
    print(f"回复: {response}\n")
    
    # === 方式 2: 注册自定义模型到注册表 ===
    print("--- 方式 2: 注册自定义模型 ---\n")
    
    # 注册 MockModel
    ModelRegistry.register("mock", MockModel)
    ModelRegistry.register("echo", EchoModel)
    
    # 通过 load_model 加载
    model1 = load_model("mock", model_name="mock-v1")
    model2 = load_model("echo", model_name="echo-v1")
    
    print("已注册模型:")
    print(f"  - mock: {model1.get_model_info()}")
    print(f"  - echo: {model2.get_model_info()}\n")
    
    # === 方式 3: 在 Agent 中使用自定义模型 ===
    print("--- 方式 3: Agent 使用自定义模型 ---\n")
    
    # 使用 MockModel
    agent_mock = SimpleAgent(
        model=mock_model,
        verbose=True
    )
    
    thread1 = Thread()
    response = agent_mock.run("今天天气怎么样？", thread1)
    print(f"\nMockModel 回答: {response}\n")
    
    # 使用 EchoModel
    agent_echo = SimpleAgent(
        model=model2,
        verbose=True
    )
    
    thread2 = Thread()
    response = agent_echo.run("这是一个测试消息", thread2)
    print(f"\nEchoModel 回答: {response}\n")
    
    # === 方式 4: 流式输出 ===
    print("--- 方式 4: 流式输出 ---\n")
    
    agent_stream = SimpleAgent(
        model=mock_model,
        stream=True
    )
    
    thread3 = Thread()
    print("流式输出: ", end="")
    response = agent_stream.run("请介绍一下 AI", thread3)
    print("\n")
    
    # === 方式 5: 使用字符串格式指定模型 ===
    print("--- 方式 5: 字符串格式指定模型 ---\n")
    
    # 可以使用 "provider:model_name" 格式
    agent_str = SimpleAgent(
        model="mock:mock-gpt",  # 会尝试从注册表加载
        verbose=False
    )
    
    thread4 = Thread()
    response = agent_str.run("你好", thread4)
    print(f"回答: {response}\n")
    
    # === 场景: 自定义模型用于测试 ===
    print("--- 场景: 用于单元测试 ---\n")
    
    class TestableModel(ModelInterface):
        """可测试的模型（返回预设响应）"""
        
        def __init__(self, model_name: str, **config):
            super().__init__(model_name, **config)
            self.responses = config.get("responses", [])
            self.current_index = 0
        
        def run(self, messages: List[Dict[str, str]], **kwargs) -> str:
            if self.current_index < len(self.responses):
                response = self.responses[self.current_index]
                self.current_index += 1
                return response
            return "默认回复"
        
        def stream_run(self, messages: List[Dict[str, str]], **kwargs):
            yield self.run(messages, **kwargs)
    
    # 创建测试模型
    test_model = TestableModel(
        model_name="test-v1",
        responses=[
            "第一次调用的回复",
            "第二次调用的回复",
            "第三次调用的回复"
        ]
    )
    
    test_agent = SimpleAgent(model=test_model)
    
    for i in range(3):
        thread = Thread()
        response = test_agent.run(f"测试消息 {i+1}", thread)
        print(f"调用 {i+1}: {response}")
    
    print("\n提示: 自定义模型特别适合用于:")
    print("  1. 单元测试（无需调用真实 API）")
    print("  2. 原型开发（快速验证逻辑）")
    print("  3. 集成第三方 LLM（包装其他 API）")
    print("  4. 本地模型（调用本地部署的模型）")

if __name__ == "__main__":
    main()

