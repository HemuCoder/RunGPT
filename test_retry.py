"""
测试网络重试机制

模拟网络错误，验证 UnifiedProvider 的自动重试功能。
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from rungpt.models.unified_provider import UnifiedProvider
from unittest.mock import patch, MagicMock
import requests
import logging

# 启用日志查看重试过程
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_retry_on_timeout():
    """测试超时重试"""
    print("\n" + "="*70)
    print("测试 1: 网络超时自动重试")
    print("="*70)
    
    provider = UnifiedProvider(
        model_name="gpt-4o",
        api_key="test_key",
        base_url="https://test.example.com/v1"
    )
    
    # 模拟：前 2 次超时，第 3 次成功
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "成功响应"}}]
    }
    
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise requests.exceptions.Timeout("模拟超时")
        return mock_response
    
    with patch('requests.post', side_effect=side_effect):
        result = provider.run([{"role": "user", "content": "测试"}])
        print(f"✅ 成功获得响应: {result}")
        print(f"📊 总共调用次数: {call_count}")
        assert call_count == 3, "应该重试 2 次后成功"


def test_max_retries_exceeded():
    """测试超过最大重试次数"""
    print("\n" + "="*70)
    print("测试 2: 超过最大重试次数")
    print("="*70)
    
    provider = UnifiedProvider(
        model_name="gpt-4o",
        api_key="test_key",
        base_url="https://test.example.com/v1"
    )
    
    # 模拟：一直超时
    with patch('requests.post', side_effect=requests.exceptions.Timeout("持续超时")):
        try:
            provider.run([{"role": "user", "content": "测试"}])
            assert False, "应该抛出 TimeoutError"
        except TimeoutError as e:
            print(f"✅ 正确抛出异常: {e}")
            assert "重试 3 次后失败" in str(e)


def test_no_retry_on_http_error():
    """测试 HTTP 错误不重试"""
    print("\n" + "="*70)
    print("测试 3: HTTP 错误不重试")
    print("="*70)
    
    provider = UnifiedProvider(
        model_name="gpt-4o",
        api_key="test_key",
        base_url="https://test.example.com/v1"
    )
    
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        error = requests.exceptions.HTTPError("401 Unauthorized")
        error.response = MagicMock(status_code=401)
        raise error
    
    with patch('requests.post', side_effect=side_effect):
        try:
            provider.run([{"role": "user", "content": "测试"}])
            assert False, "应该抛出 RuntimeError"
        except RuntimeError as e:
            print(f"✅ 正确抛出异常: {e}")
            print(f"📊 只调用了 {call_count} 次（不重试）")
            assert call_count == 1, "HTTP 错误不应该重试"


if __name__ == "__main__":
    test_retry_on_timeout()
    test_max_retries_exceeded()
    test_no_retry_on_http_error()
    
    print("\n" + "="*70)
    print("✅ 所有测试通过！")
    print("="*70)
