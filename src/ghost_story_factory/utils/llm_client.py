"""轻量级 LLM 客户端

职责：
- 提供统一的 LLM 调用接口（支持 Kimi / OpenAI）
- 完整的 request/response 日志记录
- 统一的错误处理和重试策略
- 不做 JSON 解析（只负责可靠地拿回文本）

设计原则：
- 单一职责：prompt -> str
- 最小依赖：requests 或官方 SDK
- 可观测性：完整日志
- 可测试性：易于 mock
"""

from __future__ import annotations

import os
import time
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

# 使用项目现有的日志工具
try:
    from .logging_utils import get_logger
    logger, _ = get_logger()  # get_logger() 返回 (logger, log_file_path)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """LLM 客户端错误基类"""
    pass


class LLMTimeoutError(LLMClientError):
    """LLM 调用超时"""
    pass


class LLMAPIError(LLMClientError):
    """LLM API 错误（网络、配额、限流等）"""
    pass


class LLMClient:
    """轻量级 LLM 客户端

    示例：
        >>> client = LLMClient(provider="kimi")
        >>> response = client.call(
        ...     prompt="你好，请生成一个 JSON 对象",
        ...     model="kimi-k2-0905-preview",
        ...     max_tokens=16000,
        ...     temperature=0.7,
        ... )
    """

    def __init__(self, provider: str = "kimi") -> None:
        """初始化 LLM 客户端

        Args:
            provider: 提供商，"kimi", "kimi-coding" 或 "openai"

        Raises:
            ValueError: 如果 provider 不支持或缺少 API Key
        """
        self.provider = provider.lower()

        if self.provider not in ("kimi", "kimi-coding", "openai"):
            raise ValueError(f"不支持的 provider: {provider}，仅支持 'kimi', 'kimi-coding' 或 'openai'")

        # 读取配置
        self._load_config()

        # 请求计数器（用于日志）
        self._request_count = 0

    def _load_config(self) -> None:
        """从环境变量加载配置"""
        if self.provider == "kimi":
            self.api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Kimi provider 需要设置 KIMI_API_KEY 或 MOONSHOT_API_KEY 环境变量"
                )

            self.base_url = os.getenv(
                "KIMI_API_BASE",
                os.getenv("MOONSHOT_API_URL", "https://api.moonshot.cn/v1")
            )
            self.default_model = os.getenv(
                "KIMI_MODEL",
                os.getenv("MOONSHOT_MODEL", "kimi-k2-0905-preview")
            )
            self.api_format = "openai"  # Kimi 使用 OpenAI 格式

        elif self.provider == "kimi-coding":
            # Kimi Coding 会员 API（使用 Anthropic 格式）
            self.api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Kimi Coding provider 需要设置 KIMI_API_KEY 环境变量"
                )

            self.base_url = os.getenv(
                "KIMI_API_BASE",
                "https://api.kimi.com/coding/v1"
            )
            self.default_model = os.getenv(
                "KIMI_MODEL",
                "kimi-for-coding"
            )
            self.api_format = "anthropic"  # Kimi Coding 使用 Anthropic 格式

        elif self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI provider 需要设置 OPENAI_API_KEY 环境变量")

            self.base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
            if not self.base_url:
                self.base_url = "https://api.openai.com/v1"

            self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o")
            self.api_format = "openai"

        else:
            raise ValueError(
                f"不支持的 provider: {self.provider}，仅支持 'kimi', 'kimi-coding', 'openai'"
            )

        # 超时配置（秒）：支持渐进式超时
        self.timeout_schedule = self._load_timeout_schedule()

        # 重试配置
        self.max_retries = self._load_retry_count()
        self.retry_delay = float(os.getenv("LLM_RETRY_DELAY", "2.0"))  # 指数退避起点
        self.retry_max_delay = float(os.getenv("LLM_RETRY_MAX_DELAY", "60.0"))  # 退避上限  # 退避上限

    def _load_timeout_schedule(self) -> List[int]:
        """加载超时阶梯配置

        优先级：
        1. LLM_TIMEOUTS（逗号分隔）：显式超时阶梯
        2. LLM_TIMEOUT：单一超时（保持向后兼容）
        3. 默认渐进式阶梯：[60, 120, 180]
        """
        default_schedule = [60, 120, 180]
        timeout_env = os.getenv("LLM_TIMEOUTS")

        if timeout_env:
            timeouts = [
                int(item.strip()) for item in timeout_env.split(",") if item.strip()
            ]
        elif "LLM_TIMEOUT" in os.environ:
            # 兼容旧配置：单一超时
            timeouts = [int(os.getenv("LLM_TIMEOUT", "180"))]
        else:
            timeouts = default_schedule

        # 兜底，避免配置为空
        sanitized = [t for t in timeouts if t > 0]
        return sanitized or default_schedule

    def _load_retry_count(self) -> int:
        """加载重试次数

        - 如果显式设置 LLM_MAX_RETRIES，直接使用
        - 否则：
          * 指定了 LLM_TIMEOUTS：默认 len(timeouts)-1
          * 指定了 LLM_TIMEOUT：保持旧行为，默认 1 次重试
          * 全默认：匹配默认阶梯，默认 2 次重试（共 3 次尝试）
        """
        explicit = os.getenv("LLM_MAX_RETRIES")
        if explicit is not None:
            return int(explicit)

        if "LLM_TIMEOUTS" in os.environ:
            return max(len(self.timeout_schedule) - 1, 0)

        if "LLM_TIMEOUT" in os.environ:
            return 1  # 兼容旧逻辑：单一超时仍然保留 1 次重试

        return max(len(self.timeout_schedule) - 1, 0)

    def call(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 16000,
        temperature: float = 0.7,
    ) -> str:
        """调用 LLM 并返回响应文本

        Args:
            prompt: 提示词
            model: 模型名称，不传则使用默认模型
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            str: LLM 返回的文本

        Raises:
            LLMTimeoutError: 超时
            LLMAPIError: API 错误
            LLMClientError: 其他客户端错误
        """
        model = model or self.default_model
        self._request_count += 1
        request_id = f"{self.provider}-{self._request_count}-{int(time.time())}"

        # 记录请求开始
        logger.info(
            f"[LLMClient] Request {request_id} | "
            f"provider={self.provider} model={model} "
            f"max_tokens={max_tokens} temp={temperature}"
        )
        logger.debug(f"[LLMClient] Request {request_id} | Prompt snippet: {self._snippet(prompt, 400)}")

        attempt_timeouts = self._build_attempt_timeouts()
        total_attempts = len(attempt_timeouts)
        last_error = None

        for attempt_index, timeout in enumerate(attempt_timeouts, start=1):
            try:
                response_text = self._call_internal(
                    prompt, model, max_tokens, temperature, request_id, timeout
                )

                # 记录成功响应
                logger.info(f"[LLMClient] Request {request_id} | Success | Response length: {len(response_text)}")
                logger.debug(f"[LLMClient] Request {request_id} | Response snippet: {self._snippet(response_text, 400)}")

                return response_text

            except Exception as e:
                last_error = e

                # 记录错误
                logger.error(
                    f"[LLMClient] Request {request_id} | Attempt {attempt_index}/{total_attempts} failed | "
                    f"Error: {type(e).__name__}: {str(e)}"
                )

                # 最后一次尝试，不再重试
                if attempt_index >= total_attempts:
                    break

                # 重试延迟
                next_timeout = attempt_timeouts[attempt_index]
                delay = self._compute_backoff(attempt_index)
                logger.info(
                    f"[LLMClient] Request {request_id} | Retrying in {delay}s with timeout={next_timeout}s..."
                )
                time.sleep(delay)

        # 所有重试都失败
        logger.error(
            f"[LLMClient] Request {request_id} | All {self.max_retries + 1} attempts failed | "
            f"Last error: {type(last_error).__name__}: {str(last_error)}"
        )

        # 包装错误
        timeout_errors: tuple = ()
        try:
            import requests
            timeout_errors = (
                requests.Timeout,
                getattr(requests.exceptions, "ReadTimeout", requests.Timeout),
                getattr(requests.exceptions, "ConnectTimeout", requests.Timeout),
            )
        except Exception:
            timeout_errors = ()

        if isinstance(last_error, timeout_errors) or "timeout" in str(last_error).lower():
            raise LLMTimeoutError(f"LLM 调用超时: {last_error}") from last_error
        else:
            raise LLMAPIError(f"LLM API 错误: {last_error}") from last_error

    def _call_anthropic_format(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        request_id: str,
        timeout: int,
    ) -> str:
        """使用 Anthropic Messages API 格式调用（用于 Kimi Coding）

        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大 token 数
            temperature: 温度参数
            request_id: 请求 ID（用于日志）
            timeout: 超时时间（秒）

        Returns:
            str: LLM 返回的文本

        Raises:
            Exception: 任何 HTTP/API 错误
        """
        import requests

        # 构建请求
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,  # Anthropic 使用 x-api-key
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        # 发送请求
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )

        # 检查 HTTP 状态码
        if not response.ok:
            error_detail = response.text[:500] if response.text else "No error detail"
            raise LLMAPIError(
                f"HTTP {response.status_code} | URL: {url} | Detail: {error_detail}"
            )

        # 解析响应
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise LLMAPIError(f"Failed to parse JSON response: {e}") from e

        # 提取文本（Anthropic 格式：data.content[0].text）
        try:
            content = data["content"][0]["text"]
            if not isinstance(content, str):
                raise LLMAPIError(f"Unexpected content type: {type(content)}")
            return content
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"[LLMClient] Request {request_id} | Invalid response structure: {data}")
            raise LLMAPIError(f"Invalid response structure: {e}") from e

    def _call_internal(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        request_id: str,
        timeout: int,
    ) -> str:
        """内部调用逻辑（单次尝试）

        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大 token 数
            temperature: 温度参数
            request_id: 请求 ID（用于日志）
            timeout: 超时时间（秒）

        Returns:
            str: LLM 返回的文本

        Raises:
            Exception: 任何 HTTP/API 错误
        """
        # 根据 API 格式选择调用方法
        if self.api_format == "anthropic":
            return self._call_anthropic_format(
                prompt, model, max_tokens, temperature, request_id, timeout
            )
        
        # 默认使用 OpenAI 格式
        import requests

        # 构建请求
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # 发送请求
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )

        # 检查 HTTP 状态码
        if not response.ok:
            error_detail = response.text[:500] if response.text else "No error detail"
            raise LLMAPIError(
                f"HTTP {response.status_code} | URL: {url} | Detail: {error_detail}"
            )

        # 解析响应
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise LLMAPIError(f"Failed to parse JSON response: {e}") from e

        # 提取文本
        try:
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise LLMAPIError(f"Unexpected content type: {type(content)}")
            return content
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"[LLMClient] Request {request_id} | Invalid response structure: {data}")
            raise LLMAPIError(f"Invalid response structure: {e}") from e

    def _snippet(self, text: str, max_chars: int) -> str:
        """生成文本片段（用于日志）

        Args:
            text: 原始文本
            max_chars: 最大字符数

        Returns:
            str: 截断后的文本片段
        """
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "...[截断]"

    def _build_attempt_timeouts(self) -> List[int]:
        """根据配置生成尝试序列的超时值"""
        timeouts = list(self.timeout_schedule)
        target_attempts = self.max_retries + 1

        if not timeouts:
            timeouts = [60, 120, 180]

        if len(timeouts) >= target_attempts:
            return timeouts[:target_attempts]

        # 阶梯不足时重复最后一个值补齐
        last_timeout = timeouts[-1]
        while len(timeouts) < target_attempts:
            timeouts.append(last_timeout)
        return timeouts

    def _compute_backoff(self, attempt_index: int) -> float:
        """指数退避：attempt_index 从 1 开始表示第 N 次尝试"""
        delay = self.retry_delay * (2 ** (attempt_index - 1))
        return min(delay, self.retry_max_delay)


# 工厂函数（便于测试和依赖注入）
def create_llm_client(provider: Optional[str] = None) -> LLMClient:
    """创建 LLM 客户端实例

    Args:
        provider: 提供商，不传则根据环境变量自动选择

    Returns:
        LLMClient: 客户端实例

    Raises:
        ValueError: 如果没有可用的 provider
    """
    if provider:
        return LLMClient(provider=provider)

    # 检查环境变量 LLM_PROVIDER（支持显式指定）
    env_provider = os.getenv("LLM_PROVIDER", "").lower()
    if env_provider in ("kimi", "kimi-coding", "openai"):
        return LLMClient(provider=env_provider)

    # 自动检测：优先使用 Kimi Coding（如果配置了 Coding base URL）
    kimi_base = os.getenv("KIMI_API_BASE", "")
    if "coding" in kimi_base.lower() and (os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")):
        return LLMClient(provider="kimi-coding")

    # 回退到普通 Kimi
    if os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY"):
        return LLMClient(provider="kimi")

    # 回退到 OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return LLMClient(provider="openai")

    raise ValueError(
        "未检测到可用的 API Key。请设置 KIMI_API_KEY 或 OPENAI_API_KEY 环境变量"
    )
