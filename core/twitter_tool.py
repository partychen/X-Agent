"""推文获取工具 - 提供给 LangChain Agent 调用"""

import logging
import os
from typing import List, Dict, Any

from langchain_core.tools import tool

from fetcher.twitter_api import TwitterApiFetcher
from fetcher.twitter_scraper import TwitterScraper

logger = logging.getLogger(__name__)

NITTER_INSTANCES = [u.strip() for u in os.getenv("NITTER_INSTANCES", "https://xcancel.com").split(",") if u.strip()]
PROXY_URL = os.getenv("PROXY_URL", "").strip()


def _is_error_result(result: List[Dict[str, Any]]) -> bool:
    """判断返回结果是否为错误（API 失败、token 用尽等）"""
    return not result or (len(result) == 1 and result[0].get("text", "").startswith("Error:"))


def _fetch_via_scraper(username: str, count: int) -> List[Dict[str, Any]]:
    """通过 Playwright/Nitter 抓取推文"""
    return TwitterScraper(NITTER_INSTANCES, PROXY_URL).get_tweets(username, count)


@tool
def fetch_user_tweets(username: str, count: int = 10) -> List[Dict[str, Any]]:
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
    logger.info(f"{'=' * 60}")
    logger.info(f"调用工具: fetch_user_tweets | username='{username}', count={count}")

    token = os.getenv("TWITTER_BEARER_TOKEN")

    if token:
        logger.info("检测到 TWITTER_BEARER_TOKEN，优先使用官方 API")
        result = TwitterApiFetcher(token).get_tweets(username, count)

        if not _is_error_result(result):
            logger.info(f"API 成功，返回 {len(result)} 条推文")
            logger.info(f"{'=' * 60}")
            return result

        logger.warning(f"API 失败: {result[0].get('text', '') if result else 'Empty'}，Fallback 到 Scraper")
    else:
        logger.info("未检测到 TWITTER_BEARER_TOKEN，使用 Playwright/Nitter")

    result = _fetch_via_scraper(username, count)

    logger.info(f"最终返回 {len(result)} 条推文")
    logger.info(f"{'=' * 60}")
    return result


def get_tools():
    """返回所有可用工具列表"""
    return [fetch_user_tweets]
