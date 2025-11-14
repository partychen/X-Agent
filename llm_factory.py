"""
LLM Factory - 支持多种大语言模型提供商
支持: Azure OpenAI, DeepSeek, Kimi (Moonshot), 豆包 (Doubao)
"""

import os
import logging
from typing import Optional
from abc import ABC, abstractmethod
from azure.identity import AzureCliCredential, get_bearer_token_provider
from langchain_openai import AzureChatOpenAI, ChatOpenAI

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """LLM提供商基类"""
    
    @abstractmethod
    def create_llm(self, **kwargs):
        """创建并返回LLM实例"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """返回提供商名称"""
        pass


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI 提供商"""
    
    def create_llm(self, **kwargs):
        logger.info("正在初始化 Azure OpenAI LLM...")
        token_provider = get_bearer_token_provider(
            AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
        )
        
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            max_retries=kwargs.get("max_retries", 3),
            temperature=kwargs.get("temperature", 0.1),
            top_p=kwargs.get("top_p", 0.9),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_ad_token_provider=token_provider,
        )
        logger.info(f"Azure OpenAI 初始化完成 - 部署: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
        return llm
    
    def get_name(self) -> str:
        return "Azure OpenAI"


class DeepSeekProvider(LLMProvider):
    """DeepSeek 提供商"""
    
    def create_llm(self, **kwargs):
        logger.info("正在初始化 DeepSeek LLM...")
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量")
        
        llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            max_retries=kwargs.get("max_retries", 3),
            temperature=kwargs.get("temperature", 0.1),
            top_p=kwargs.get("top_p", 0.9),
        )
        logger.info(f"DeepSeek 初始化完成 - 模型: {os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')}")
        return llm
    
    def get_name(self) -> str:
        return "DeepSeek"


class KimiProvider(LLMProvider):
    """Kimi (Moonshot) 提供商"""
    
    def create_llm(self, **kwargs):
        logger.info("正在初始化 Kimi (Moonshot) LLM...")
        
        api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            raise ValueError("未设置 KIMI_API_KEY 或 MOONSHOT_API_KEY 环境变量")
        
        llm = ChatOpenAI(
            model=os.getenv("KIMI_MODEL", "moonshot-v1-8k"),
            api_key=api_key,
            base_url=os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
            max_retries=kwargs.get("max_retries", 3),
            temperature=kwargs.get("temperature", 0.3),
        )
        logger.info(f"Kimi 初始化完成 - 模型: {os.getenv('KIMI_MODEL', 'moonshot-v1-8k')}")
        return llm
    
    def get_name(self) -> str:
        return "Kimi (Moonshot)"


class DoubaoProvider(LLMProvider):
    """豆包 (Doubao/字节跳动) 提供商"""
    
    def create_llm(self, **kwargs):
        logger.info("正在初始化 豆包 (Doubao) LLM...")
        
        api_key = os.getenv("DOUBAO_API_KEY") or os.getenv("BYTEDANCE_API_KEY")
        if not api_key:
            raise ValueError("未设置 DOUBAO_API_KEY 或 BYTEDANCE_API_KEY 环境变量")
        
        llm = ChatOpenAI(
            model=os.getenv("DOUBAO_MODEL", "doubao-pro-4k"),
            api_key=api_key,
            base_url=os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
            max_retries=kwargs.get("max_retries", 3),
            temperature=kwargs.get("temperature", 0.1),
        )
        logger.info(f"豆包 初始化完成 - 模型: {os.getenv('DOUBAO_MODEL', 'doubao-pro-4k')}")
        return llm
    
    def get_name(self) -> str:
        return "豆包 (Doubao)"


class LLMFactory:
    """LLM工厂类 - 根据配置创建不同的LLM实例"""
    
    _providers = {
        "azure_openai": AzureOpenAIProvider(),
        "deepseek": DeepSeekProvider(),
        "kimi": KimiProvider(),
        "moonshot": KimiProvider(),  # Moonshot 是 Kimi 的别名
        "doubao": DoubaoProvider(),
        "bytedance": DoubaoProvider(),  # ByteDance 是豆包的别名
    }
    
    @classmethod
    def create_llm(cls, provider_name: Optional[str] = None, **kwargs):
        """
        创建LLM实例
        
        Args:
            provider_name: LLM提供商名称，支持:
                - "azure_openai": Azure OpenAI
                - "deepseek": DeepSeek
                - "kimi" 或 "moonshot": Kimi (Moonshot)
                - "doubao" 或 "bytedance": 豆包 (Doubao)
                如果为None，则从环境变量 LLM_PROVIDER 读取，默认为 "azure_openai"
            **kwargs: 传递给LLM的其他参数 (temperature, max_retries, top_p等)
        
        Returns:
            LLM实例
        
        Raises:
            ValueError: 当提供商名称无效时
        """
        if provider_name is None:
            provider_name = os.getenv("LLM_PROVIDER", "azure_openai").lower()
        else:
            provider_name = provider_name.lower()
        
        logger.info(f"使用 LLM 提供商: {provider_name}")
        
        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"不支持的 LLM 提供商: {provider_name}. "
                f"支持的提供商: {available}"
            )
        
        provider = cls._providers[provider_name]
        return provider.create_llm(**kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """获取所有可用的提供商名称"""
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_display_names(cls) -> dict:
        """获取提供商的显示名称映射"""
        return {
            key: provider.get_name() 
            for key, provider in cls._providers.items()
        }


def get_llm(provider_name: Optional[str] = None, **kwargs):
    """
    便捷函数：创建LLM实例
    
    Args:
        provider_name: LLM提供商名称 (azure_openai, deepseek, kimi, doubao等)
        **kwargs: 传递给LLM的其他参数
    
    Returns:
        LLM实例
    """
    return LLMFactory.create_llm(provider_name, **kwargs)
