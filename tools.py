from langchain_core.tools import tool
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page
import time
import sys
import asyncio

# 修复 Python 3.13 在 Windows 上的事件循环策略问题
if sys.platform == "win32" and sys.version_info >= (3, 13):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def _setup_browser(playwright):
    """设置浏览器并返回页面对象"""
    browser = playwright.chromium.launch(
        headless=True,
        channel="chrome",
        args=['--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={'width': 1920, 'height': 1080}
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
    return browser, page


def _extract_post_data(tweet_element) -> Dict[str, str]:
    """从推文元素中提取数据"""
    text_elem = tweet_element.query_selector(".tweet-content")
    text = text_elem.inner_text() if text_elem else ""
    
    time_elem = tweet_element.query_selector(".tweet-date a")
    created_at = ""
    if time_elem:
        created_at = time_elem.get_attribute("title") or time_elem.inner_text()
    
    return {"text": text.strip(), "created_at": created_at}


def _is_duplicate(post: Dict[str, str], posts: List[Dict[str, str]]) -> bool:
    """检查推文是否已存在"""
    return any(p["text"] == post["text"] and p["created_at"] == post["created_at"] for p in posts)


def _load_more_tweets(page: Page) -> bool:
    """尝试加载更多推文，返回是否成功"""
    try:
        # 尝试点击 "Show more" 按钮
        show_more = page.query_selector(".show-more:not(.timeline-item), .timeline-footer .show-more")
        if show_more and show_more.is_visible():
            show_more.click()
            time.sleep(2)
            return True
        
        # 否则滚动页面
        old_count = len(page.query_selector_all("div.timeline-item"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        new_count = len(page.query_selector_all("div.timeline-item"))
        
        return new_count > old_count  # 有新内容才返回 True
    except:
        return False


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
    posts = []
    target_count = min(count, 100)
    
    try:
        with sync_playwright() as p:
            browser, page = _setup_browser(p)
            
            # 访问页面
            page.goto(f"https://nitter.net/{username}", wait_until="load", timeout=60000)
            time.sleep(3)
            
            # 滚动加载推文直到达到目标数量
            for attempt in range(10):  # 最多尝试 10 次
                tweet_elements = page.query_selector_all("div.timeline-item")
                
                # 提取推文数据
                for tweet in tweet_elements:
                    try:
                        post = _extract_post_data(tweet)
                        if post["text"] and not _is_duplicate(post, posts):
                            posts.append(post)
                            if len(posts) >= target_count:
                                break
                    except:
                        continue
                
                # 达到目标或无法加载更多时停止
                if len(posts) >= target_count or not _load_more_tweets(page):
                    break
            
            browser.close()
            
    except Exception as e:
        return [{"text": f"Error: Failed to fetch posts - {str(e)}", "created_at": ""}]
    
    return posts if posts else [{"text": f"No posts found for @{username}", "created_at": ""}]