from langchain_core.tools import tool
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page
import time
import logging
import os

# 获取日志记录器（使用模块名，这样会继承 app.py 的配置）
logger = logging.getLogger(__name__)

# 从环境变量读取配置
NITTER_INSTANCES = [url.strip() for url in os.getenv("NITTER_INSTANCES", "https://nitter.net").split(",") if url.strip()]
PROXY_URL = os.getenv("PROXY_URL", "").strip()


def _setup_browser(playwright):
    """设置浏览器并返回页面对象"""
    logger.info("正在启动浏览器（无头模式）...")
    
    launch_args = {
        "headless": True,
        "channel": "chrome",
        "args": ['--disable-blink-features=AutomationControlled']
    }
    
    if PROXY_URL:
        logger.info(f"使用代理: {PROXY_URL}")
        launch_args["proxy"] = {"server": PROXY_URL}
        
    browser = playwright.chromium.launch(**launch_args)
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={'width': 1920, 'height': 1080},
        ignore_https_errors=True,
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
    logger.info("浏览器启动完成")
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
            logger.debug("点击 'Show more' 按钮加载更多推文")
            show_more.click()
            time.sleep(2)
            return True
        
        # 否则滚动页面
        old_count = len(page.query_selector_all("div.timeline-item"))
        logger.debug(f"滚动页面加载更多推文（当前: {old_count} 条）")
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
    logger.info(f"=" * 60)
    logger.info(f"调用工具: get_user_post")
    logger.info(f"参数: username='{username}', count={count}")
    logger.info(f"=" * 60)
    
    posts = []
    target_count = min(count, 100)
    
    try:
        with sync_playwright() as p:
            browser, page = _setup_browser(p)
            
            # 尝试不同的 Nitter 实例
            success = False
            for instance in NITTER_INSTANCES:
                try:
                    url = f"{instance}/{username}"
                    logger.info(f"正在尝试访问: {url}")
                    page.goto(url, wait_until="load", timeout=60000)
                    logger.info(f"页面加载完成，等待3秒...")
                    time.sleep(3)
                    
                    # 检查是否成功加载（是否有推文）
                    if page.query_selector("div.timeline-item"):
                        logger.info(f"成功连接到实例: {instance}")
                        success = True
                        break
                    else:
                        logger.warning(f"实例 {instance} 未返回推文，尝试下一个...")
                except Exception as e:
                    logger.warning(f"访问实例 {instance} 失败: {str(e)}")
                    continue
            
            if not success:
                raise Exception("所有 Nitter 实例均无法访问或未返回数据")
            
            # 滚动加载推文直到达到目标数量
            logger.info(f"开始抓取推文，目标数量: {target_count}")
            for attempt in range(10):  # 最多尝试 10 次
                tweet_elements = page.query_selector_all("div.timeline-item")
                logger.info(f"第 {attempt + 1} 轮抓取，页面上共有 {len(tweet_elements)} 个推文元素")
                
                # 提取推文数据
                for tweet in tweet_elements:
                    try:
                        post = _extract_post_data(tweet)
                        if post["text"] and not _is_duplicate(post, posts):
                            posts.append(post)
                            logger.debug(f"成功提取推文 #{len(posts)}: {post['text'][:50]}...")
                            if len(posts) >= target_count:
                                break
                    except:
                        continue
                
                logger.info(f"当前已收集 {len(posts)}/{target_count} 条推文")
                
                # 达到目标或无法加载更多时停止
                if len(posts) >= target_count:
                    logger.info(f"已达到目标数量，停止抓取")
                    break
                    
                if not _load_more_tweets(page):
                    logger.info(f"无法加载更多推文，停止抓取")
                    break
            
            browser.close()
            logger.info(f"浏览器已关闭")
            
    except Exception as e:
        logger.error(f"抓取失败: {str(e)}", exc_info=True)
        return [{"text": f"Error: Failed to fetch posts - {str(e)}", "created_at": ""}]
    
    result = posts if posts else [{"text": f"No posts found for @{username}", "created_at": ""}]
    logger.info(f"最终返回 {len(result)} 条推文")
    logger.info(f"=" * 60)
    return result