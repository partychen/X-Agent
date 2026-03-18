"""测试脚本 - 直接调用 _fetch_via_scraper 获取 elonmusk 的推文"""

import logging
import os
import sys
from dotenv import load_dotenv

# 将项目根目录加入 sys.path，确保从 tests/ 目录运行时也能正确导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 从项目根目录加载 .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fetcher.twitter_scraper import TwitterScraper

# 配置日志，方便看到完整的抓取过程
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ========== 从 .env 读取配置 ==========
NITTER_INSTANCES = [u.strip() for u in os.getenv("NITTER_INSTANCES", "https://nitter.net").split(",") if u.strip()]
PROXY_URL = os.getenv("PROXY_URL", "").strip()
TARGET_USERNAME = os.getenv("TARGET_USERNAME", "wanjunxie").strip() or "wanjunxie"
TWEET_COUNT = int(os.getenv("TWEET_COUNT", "5"))
SCRAPER_HEADLESS = os.getenv("SCRAPER_HEADLESS", "false").strip().lower() not in {"0", "false", "no", "off"}
# ======================================

if __name__ == "__main__":
    print(f"抓取 @{TARGET_USERNAME} 的推文 (实例: {NITTER_INSTANCES[0]}, 无头: {SCRAPER_HEADLESS})")

    scraper = TwitterScraper(
        NITTER_INSTANCES,
        PROXY_URL,
        headless=SCRAPER_HEADLESS,
    )
    result = scraper.get_tweets(TARGET_USERNAME, TWEET_COUNT)

    def _is_error_result(result):
        return bool(result) and all(str(item.get("text", "")).startswith("Error:") for item in result)

    if _is_error_result(result):
        print(f"❌ 抓取失败: {result[0].get('text', 'Unknown error')}")
        sys.exit(1)

    print(f"✅ 共获取 {len(result)} 条推文")
    for i, tweet in enumerate(result, 1):
        created = tweet.get("created_at", "N/A")
        text = tweet.get("text", "N/A")[:80]
        print(f"  {i}. [{created}] {text}...")
