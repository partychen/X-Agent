"""Twitter API Fetcher - 通过 X (Twitter) 官方 API v2 获取推文"""

import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

_EMPTY_TIME = ""


def _error(msg: str) -> List[Dict[str, Any]]:
    """构造统一的错误返回"""
    return [{"text": f"Error: {msg}", "created_at": _EMPTY_TIME}]


class TwitterApiFetcher:
    """通过 X (Twitter) 官方 API v2 获取推文"""

    _TIMEOUT = 15

    def __init__(self, token: str):
        self.token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "v2UserTweetsPython",
        }

    def _check_response(self, resp: requests.Response, action: str) -> str | None:
        """检查 HTTP 响应状态码，返回错误信息或 None（表示正常）"""
        code = resp.status_code
        if code == 200:
            return None
        messages = {
            429: "API rate limit exceeded (429) - token quota exhausted",
            401: "API authentication failed (401) - invalid or expired token",
            403: "API access forbidden (403) - insufficient permissions",
        }
        if code in messages:
            logger.warning(f"{action}: {messages[code]}")
            return messages[code]
        logger.error(f"{action}: HTTP {code} {resp.text}")
        return f"{action} - HTTP {code}"

    def get_tweets(self, username: str, count: int) -> List[Dict[str, Any]]:
        """使用 X.com API 获取推文"""
        logger.info(f"使用 X.com API 获取用户 {username} 的推文")

        try:
            # 1. 获取用户 ID
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            user_resp = requests.get(user_url, headers=self._headers, timeout=self._TIMEOUT)

            if err := self._check_response(user_resp, "获取用户 ID"):
                return _error(err)

            user_data = user_resp.json()
            if "data" not in user_data:
                return _error(f"User {username} not found")

            user_id = user_data["data"]["id"]
            logger.info(f"获取到用户 ID: {user_id}")

            # 2. 获取推文
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                "max_results": max(5, min(count, 100)),
                "tweet.fields": "created_at,text",
            }

            tweets_resp = requests.get(tweets_url, headers=self._headers, params=params, timeout=self._TIMEOUT)

            if err := self._check_response(tweets_resp, "获取推文"):
                return _error(err)

            posts = [
                {"text": t["text"], "created_at": t.get("created_at", "")}
                for t in tweets_resp.json().get("data", [])
            ]

            logger.info(f"API 成功获取 {len(posts)} 条推文")
            return posts if posts else _error(f"No posts found for @{username}")

        except requests.exceptions.Timeout:
            logger.error("API 请求超时")
            return _error("API request timed out")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"API 连接失败: {e}")
            return _error(f"API connection failed - {e}")

        except Exception as e:
            logger.error(f"API 请求异常: {e}", exc_info=True)
            return _error(f"API request exception - {e}")
