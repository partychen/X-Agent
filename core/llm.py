"""LLM 初始化 - 连接 OpenAI 兼容的模型服务"""

import os
import logging
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def create_llm(**kwargs):
    """
    创建 LLM 实例

    通过环境变量配置:
        - LOCAL_LLM_BASE_URL: 模型服务地址 (默认: http://localhost:11434/v1)
        - LOCAL_LLM_MODEL: 模型名称 (默认: qwen2.5:7b)
        - LOCAL_LLM_API_KEY: API Key (默认: not-needed)

    Args:
        **kwargs: 传递给 ChatOpenAI 的其他参数 (temperature, max_retries, top_p 等)

    Returns:
        ChatOpenAI 实例
    """
    base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:7b")
    api_key = os.getenv("LOCAL_LLM_API_KEY", "not-needed")

    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        max_retries=kwargs.get("max_retries", 3),
        temperature=kwargs.get("temperature", 0.1),
        top_p=kwargs.get("top_p", 0.9),
    )

    logger.info(f"LLM 初始化完成 - 模型: {model}, 地址: {base_url}")
    return llm
