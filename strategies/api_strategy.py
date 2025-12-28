import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ApiStrategy:
    def __init__(self, token: str):
        self.token = token

    def get_tweets(self, username: str, count: int) -> List[Dict[str, Any]]:
        """使用 X.com API 获取推文"""
        logger.info(f"使用 X.com API 获取用户 {username} 的推文")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "v2UserTweetsPython"
        }
        
        try:
            # 1. 获取用户 ID
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            logger.info(f"请求用户 ID: {user_url}")
            user_resp = requests.get(user_url, headers=headers)
            
            if user_resp.status_code != 200:
                logger.error(f"API 获取用户 ID 失败: {user_resp.status_code} {user_resp.text}")
                return [{"text": f"Error: API failed to get user ID - {user_resp.text}", "created_at": ""}]
                
            user_data = user_resp.json()
            if "data" not in user_data:
                return [{"text": f"Error: User {username} not found", "created_at": ""}]
                
            user_id = user_data["data"]["id"]
            logger.info(f"获取到用户 ID: {user_id}")
            
            # 2. 获取推文
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            # API 限制 max_results 在 5 到 100 之间
            max_results = max(5, min(count, 100))
            
            params = {
                "max_results": max_results,
                "tweet.fields": "created_at,text"
            }
            
            logger.info(f"请求推文列表: {tweets_url}")
            tweets_resp = requests.get(tweets_url, headers=headers, params=params)
            
            if tweets_resp.status_code != 200:
                logger.error(f"API 获取推文失败: {tweets_resp.status_code} {tweets_resp.text}")
                return [{"text": f"Error: API failed to get tweets - {tweets_resp.text}", "created_at": ""}]
                
            tweets_data = tweets_resp.json()
            posts = []
            
            if "data" in tweets_data:
                for t in tweets_data["data"]:
                    posts.append({
                        "text": t["text"],
                        "created_at": t.get("created_at", "")
                    })
            
            logger.info(f"API 成功获取 {len(posts)} 条推文")
            return posts if posts else [{"text": f"No posts found for @{username}", "created_at": ""}]
            
        except Exception as e:
            logger.error(f"API 请求发生异常: {str(e)}", exc_info=True)
            return [{"text": f"Error: API request exception - {str(e)}", "created_at": ""}]
