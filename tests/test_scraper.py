"""测试脚本 - 直接调用 _fetch_via_scraper 获取 elonmusk 的推文"""

import logging
import json
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
SCRAPER_USER_DATA_DIR = os.getenv("SCRAPER_USER_DATA_DIR", "").strip()
# ======================================

if __name__ == "__main__":
    print("=" * 60)
    print(f"测试: 通过 Playwright/Nitter 抓取 @{TARGET_USERNAME} 的推文")
    print(f"Nitter 实例: {NITTER_INSTANCES}")
    print(f"代理: {PROXY_URL}")
    print(f"无头模式: {SCRAPER_HEADLESS}")
    print(f"浏览器资料目录: {SCRAPER_USER_DATA_DIR or '默认'}")
    print("=" * 60)

    scraper = TwitterScraper(
        NITTER_INSTANCES,
        PROXY_URL,
        headless=SCRAPER_HEADLESS,
        user_data_dir=SCRAPER_USER_DATA_DIR or None,
    )
    result = scraper.get_tweets(TARGET_USERNAME, TWEET_COUNT)

    def _is_error_result(result):
        return bool(result) and all(str(item.get("text", "")).startswith("Error:") for item in result)

    if _is_error_result(result):
        print("\n" + "=" * 60)
        print("结果: 抓取失败")
        print("=" * 60)
        print(result[0].get("text", "Unknown error"))
        print("\n\n===== 完整 JSON =====")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"结果: 共获取 {len(result)} 条推文")
    print("=" * 60)

    for i, tweet in enumerate(result, 1):
        print(f"\n--- 推文 #{i} ---")
        print(f"时间: {tweet.get('created_at', 'N/A')}")
        print(f"内容: {tweet.get('text', 'N/A')[:200]}")

    # 同时输出完整 JSON 方便调试
    print("\n\n===== 完整 JSON =====")
    print(json.dumps(result, ensure_ascii=False, indent=2))
