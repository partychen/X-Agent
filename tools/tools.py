from langchain_core.tools import tool
from typing import List, Dict, Any
import logging
import os
from strategies.api_strategy import ApiStrategy
from strategies.playwright_strategy import PlaywrightStrategy

# 获取日志记录器（使用模块名，这样会继承 app.py 的配置）
logger = logging.getLogger(__name__)

# 从环境变量读取配置
NITTER_INSTANCES = [url.strip() for url in os.getenv("NITTER_INSTANCES", "https://nitter.net").split(",") if url.strip()]
PROXY_URL = os.getenv("PROXY_URL", "").strip()

@tool
def get_user_post(username: str, count: int = 10) -> List[Dict[str, Any]]:
    """获取Twitter用户的最近推文信息，用于分析用户行为和特征。
    当用户要求分析某个Twitter用户时，必须先调用此工具获取该用户的推文数据。
    
    Args:
        username: Twitter用户名（不需要包含@符号），例如：trump, elonmusk等
        count: 要获取的最近推文数量（默认：10，最大：100）
    
    Returns:
        List[Dict[str, Any]]: 推文列表，每条推文包含：
            - text: 推文内容
            - created_at: 发布时间
    """
    logger.info(f"=" * 60)
    logger.info(f"调用工具: get_user_post")
    logger.info(f"参数: username='{username}', count={count}")
    
    # 检查是否配置了 Twitter API Token
    token = os.getenv("TWITTER_BEARER_TOKEN")
    
    if token:
        logger.info("检测到 TWITTER_BEARER_TOKEN，使用官方 API 模式")
        strategy = ApiStrategy(token)
    else:
        logger.info("未检测到 TWITTER_BEARER_TOKEN，使用 Playwright/Nitter 模式")
        strategy = PlaywrightStrategy(NITTER_INSTANCES, PROXY_URL)
        
    result = strategy.get_tweets(username, count)
        
    logger.info(f"最终返回 {len(result)} 条推文")
    logger.info(f"=" * 60)
    return result