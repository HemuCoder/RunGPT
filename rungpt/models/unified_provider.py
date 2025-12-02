"""Unified Provider - 统一第三方模型平台的调用封装"""
from typing import List, Dict, Any, Optional
from .model_interface import ModelInterface
import os
import json
import requests
import time
import logging

logger = logging.getLogger(__name__)


class UnifiedProvider(ModelInterface):
    """统一模型提供者，封装第三方统一模型平台"""
    
    def __init__(
        self, 
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 300,
        **config
    ):
        """
        初始化 UnifiedProvider
        
        Args:
            model_name: 模型名称
            api_key: API 密钥（可选，默认从环境变量读取）
            base_url: API 基础 URL（可选，默认从环境变量读取）
            timeout: 请求超时时间（秒），默认 300 秒（5分钟）
            **config: 其他配置参数
        """
        super().__init__(model_name, **config)
        self.api_key = api_key or os.getenv("UNIFIED_API_KEY")
        if not self.api_key:
            raise ValueError("API Key 未设置，请通过参数或环境变量 UNIFIED_API_KEY 提供")
        self.base_url = base_url or os.getenv("UNIFIED_BASE_URL", "https://vip.dmxapi.com/v1")
        self.endpoint = f"{self.base_url}/chat/completions"
        self.timeout = timeout
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            'Accept': 'application/json',
            'Authorization': self.api_key,
            'User-Agent': 'AgentWorks/1.0.0',
            'Content-Type': 'application/json'
        }
    
    def _build_payload(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Dict[str, Any]:
        """构建请求负载"""
        return {
            "model": self.model_name,
            "stream": stream,
            "messages": messages,
            **self.config,
            **kwargs
        }
    
    def run(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        执行模型推理（非流式），带网络重试
        
        Args:
            messages: 消息列表
            **kwargs: temperature, max_tokens, top_p 等参数
            
        Returns:
            str: 模型返回内容
        """
        max_retries = 3
        retry_delay = 1.0  # 初始延迟 1 秒
        
        for attempt in range(max_retries):
            try:
                payload = self._build_payload(messages, stream=False, **kwargs)
                headers = self._build_headers()
                
                logger.debug(f"发起 LLM 请求，超时时间: {self.timeout}s")
                
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                if "choices" not in data or not data["choices"]:
                    raise ValueError(f"API 返回数据格式异常: {data}")
                
                return data["choices"][0]["message"]["content"]
            
            except (requests.exceptions.Timeout, 
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError) as e:
                # 网络相关错误：重试
                if attempt < max_retries - 1:
                    logger.warning(
                        f"网络错误 (尝试 {attempt + 1}/{max_retries}): {e.__class__.__name__}: {e}"
                    )
                    logger.info(f"等待 {retry_delay:.1f} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    # 最后一次尝试也失败
                    logger.error(f"网络错误，已达最大重试次数 ({max_retries})")
                    raise TimeoutError(f"模型调用超时（重试 {max_retries} 次后失败）: {e}")
            
            except requests.exceptions.HTTPError as e:
                # HTTP 错误（如 4xx, 5xx）：不重试，直接抛出
                raise RuntimeError(f"模型调用 HTTP 错误: {e}")
            
            except requests.exceptions.RequestException as e:
                # 其他请求异常：不重试
                raise RuntimeError(f"模型调用失败: {e}")
            
            except (KeyError, IndexError) as e:
                # 数据解析错误：不重试
                raise ValueError(f"解析模型响应失败: {e}")

    
    
    def stream_run(self, messages: List[Dict[str, str]], **kwargs):
        """
        流式执行模型推理，带网络重试
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式文本片段
        """
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                payload = self._build_payload(messages, stream=True, **kwargs)
                headers = self._build_headers()
                
                logger.debug(f"发起流式 LLM 请求，超时时间: {self.timeout}s")
                
                response = requests.post(self.endpoint, headers=headers, json=payload, stream=True, timeout=self.timeout)
                response.raise_for_status()
                
                # 成功建立连接，开始流式传输
                buffer = ""
                try:
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            buffer += chunk.decode("utf-8")
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                if line.strip() == "":
                                    continue
                                if line.startswith("data: "):
                                    data_line = line[len("data: "):].strip()
                                    if data_line == "[DONE]":
                                        return
                                    else:
                                        try:
                                            data = json.loads(data_line)
                                            if "choices" in data and len(data["choices"]) > 0:
                                                delta = data["choices"][0].get("delta", {})
                                                content = delta.get("content", "")
                                                if content:
                                                    yield content
                                        except json.JSONDecodeError:
                                            buffer = line + "\n" + buffer
                                            break
                    # 流式传输成功完成
                    return
                    
                except requests.exceptions.ChunkedEncodingError:
                    # 流式传输过程中的网络错误
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"流式传输中断 (尝试 {attempt + 1}/{max_retries}): ChunkedEncodingError"
                        )
                        logger.info(f"等待 {retry_delay:.1f} 秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(f"流式传输失败，已达最大重试次数 ({max_retries})")
                        return
                except Exception:
                    # 其他流式传输错误，直接返回
                    return
            
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                # 建立连接阶段的网络错误：重试
                if attempt < max_retries - 1:
                    logger.warning(
                        f"流式连接失败 (尝试 {attempt + 1}/{max_retries}): {e.__class__.__name__}: {e}"
                    )
                    logger.info(f"等待 {retry_delay:.1f} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"流式连接失败，已达最大重试次数 ({max_retries})")
                    raise RuntimeError(f"流式模型调用失败（重试 {max_retries} 次后失败）: {e}")
            
            except requests.exceptions.HTTPError as e:
                # HTTP 错误：不重试
                raise RuntimeError(f"流式模型调用 HTTP 错误: {e}")
            
            except requests.exceptions.RequestException as e:
                # 其他请求异常：不重试
                raise RuntimeError(f"流式模型调用失败: {e}")

    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = super().get_model_info()
        info.update({
            "base_url": self.base_url,
            "endpoint": self.endpoint,
            "has_api_key": bool(self.api_key)
        })
        return info

