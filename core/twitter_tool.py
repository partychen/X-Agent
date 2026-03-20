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

# 运行时获取模式，由前端 sidebar 设置
_fetch_mode = "auto"


def set_fetch_mode(mode: str):
    """设置获取模式（auto / api_only / scraper_only）"""
    global _fetch_mode
    _fetch_mode = mode


def _is_error_result(result: List[Dict[str, Any]]) -> bool:
    """判断返回结果是否为错误（API 失败、token 用尽等）"""
    return not result or (len(result) == 1 and result[0].get("text", "").startswith("Error:"))


def _fetch_via_api(username: str, count: int) -> List[Dict[str, Any]]:
    """通过官方 API 获取推文"""
    token = os.getenv("TWITTER_BEARER_TOKEN")
    if not token:
        return [{"text": "Error: 未配置 TWITTER_BEARER_TOKEN，无法使用 API 模式"}]
    return TwitterApiFetcher(token).get_tweets(username, count)


def _fetch_via_scraper(username: str, count: int) -> List[Dict[str, Any]]:
    """通过 Playwright/Nitter 抓取推文"""
    return TwitterScraper(NITTER_INSTANCES, PROXY_URL).get_tweets(username, count)


@tool
def fetch_user_tweets(username: str, count: int = 10) -> List[Dict[str, Any]]:
    """获取Twitter用户的最近推文信息，用于分析用户行为和特征。
    当用户要求分析某个Twitter用户时，必须先调用此工具获取该用户的推文数据。

    Args:
        username: Twitter用户名（不需要包含@符号），例如：trump, elonmusk等
        count: 要获取的最近推文数量，默认10条，最大100条。除非用户明确要求获取更多推文，否则请使用默认值20

    Returns:
        List[Dict[str, Any]]: 推文列表，每条推文包含：
            - text: 推文内容
            - created_at: 发布时间
    """
    mode = _fetch_mode
    logger.info(f"{'=' * 60}")
    logger.info(f"调用工具: fetch_user_tweets | username='{username}', count={count}, mode='{mode}'")

    if mode == "api_only":
        logger.info("模式: 仅 API")
        result = _fetch_via_api(username, count)
        logger.info(f"API 返回 {len(result)} 条推文")
        logger.info(f"{'=' * 60}")
        return result

    if mode == "scraper_only":
        logger.info("模式: 仅爬虫")
        result = _fetch_via_scraper(username, count)
        logger.info(f"爬虫返回 {len(result)} 条推文")
        logger.info(f"{'=' * 60}")
        return result

    # auto 模式：API 优先，失败回退爬虫
    token = os.getenv("TWITTER_BEARER_TOKEN")

    if token:
        logger.info("auto 模式: 检测到 TWITTER_BEARER_TOKEN，优先使用官方 API")
        result = _fetch_via_api(username, count)

        if not _is_error_result(result):
            logger.info(f"API 成功，返回 {len(result)} 条推文")
            logger.info(f"{'=' * 60}")
            return result

        logger.warning(f"API 失败: {result[0].get('text', '') if result else 'Empty'}，Fallback 到 Scraper")
    else:
        logger.info("auto 模式: 未检测到 TWITTER_BEARER_TOKEN，使用 Playwright/Nitter")

    result = _fetch_via_scraper(username, count)

    logger.info(f"最终返回 {len(result)} 条推文")
    logger.info(f"{'=' * 60}")
    return result


def get_tools():
    """返回所有可用工具列表"""
    return [fetch_user_tweets]
