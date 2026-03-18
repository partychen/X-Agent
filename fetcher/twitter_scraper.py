"""Twitter Scraper - 通过 async Playwright + Nitter 抓取推文"""

import asyncio
import logging
import os
import sys
import tempfile
import shutil
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# Windows Playwright 兼容
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed")

_ERROR = lambda msg: [{"text": f"Error: {msg}", "created_at": ""}]
_TWEET_SELECTORS = (
    "div.timeline-item",
    "article.timeline-item",
    "div.main-tweet",
)
_VERIFICATION_MARKERS = (
    "verifying your request",
    "please allow up to",
    "this process is automatic",
    "x cancelled",
)


class TwitterScraper:
    """通过 Playwright 访问 Nitter 实例抓取推文"""

    def __init__(
        self,
        nitter_instances: List[str],
        proxy_url: str = "",
        headless: bool | None = None,
    ):
        self.nitter_instances = nitter_instances
        self.proxy_url = proxy_url
        self.headless = self._resolve_headless(headless)
        self.verification_timeout_ms = int(os.getenv("SCRAPER_VERIFICATION_TIMEOUT_MS", "120000"))

    @staticmethod
    def _resolve_headless(headless: bool | None) -> bool:
        if headless is not None:
            return headless
        return os.getenv("SCRAPER_HEADLESS", "true").strip().lower() not in {"0", "false", "no", "off"}

    # ---------- async 核心 ----------

    async def _async_get_tweets(self, username: str, count: int) -> List[Dict[str, Any]]:
        target = min(count, 100)
        tmp_dir = tempfile.mkdtemp(prefix="scraper-")

        try:
            async with async_playwright() as pw:
                context = await self._launch_context(pw, tmp_dir)
                try:
                    page = await self._new_stealth_page(context)
                    page = await self._navigate_to_nitter(page, username)
                    posts = await self._scrape_tweets(page, target)
                finally:
                    await context.close()
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        if not posts:
            return [{"text": f"No posts found for @{username}", "created_at": ""}]
        return posts

    async def _launch_context(self, pw, user_data_dir: str):
        launch_opts: dict = {
            "headless": self.headless,
            "channel": "chrome",
            "ignore_default_args": ["--enable-automation"],
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-position=-32000,-32000",
            ],
            "viewport": {"width": 1440, "height": 900},
            "locale": "en-US",
            "timezone_id": "Asia/Shanghai",
            "ignore_https_errors": True,
        }
        if self.proxy_url:
            launch_opts["proxy"] = {"server": self.proxy_url}

        context = await pw.chromium.launch_persistent_context(user_data_dir, **launch_opts)
        await context.add_init_script(
            """
            // 隐藏 webdriver 标志
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // 删除自动化相关的 window 属性
            delete window.__playwright;
            delete window.__pw_manual;
            // 修复 permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);
            // 确保 chrome runtime 存在
            window.chrome = window.chrome || {};
            window.chrome.runtime = window.chrome.runtime || {};
            """
        )
        return context

    async def _new_stealth_page(self, context):
        page = context.pages[0] if context.pages else await context.new_page()
        await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"})
        return page

    async def _navigate_to_nitter(self, page, username: str):
        """依次尝试 Nitter 实例，返回成功加载的 page"""
        for instance in self.nitter_instances:
            try:
                url = f"{instance}/{username}"
                logger.info(f"尝试访问: {url}")
                try:
                    await page.goto(url, wait_until="load", timeout=60000)
                except Exception as nav_err:
                    # goto 可能因为验证页重定向而超时或报错，继续等待
                    logger.info(f"初始导航异常（可能是验证页跳转）: {nav_err}")
                    try:
                        await page.wait_for_load_state("load", timeout=30000)
                    except Exception:
                        pass
                if await self._wait_for_tweets(page, url):
                    logger.info(f"连接成功: {instance}")
                    return page
                logger.warning(
                    "%s 未返回推文，当前标题=%r, 当前 URL=%s",
                    instance,
                    await page.title(),
                    page.url,
                )
            except Exception as e:
                logger.warning(f"{instance} 失败: {e}")
        raise RuntimeError("所有 Nitter 实例均无法访问或未返回数据")

    async def _wait_for_tweets(self, page, expected_url: str, timeout: int | None = None) -> bool:
        """等待验证页跳转完成，或直到页面上出现推文节点。"""
        timeout = timeout or self.verification_timeout_ms
        deadline = asyncio.get_running_loop().time() + timeout / 1000
        saw_verification_page = False

        while asyncio.get_running_loop().time() < deadline:
            try:
                if await self._has_tweets(page):
                    return True

                page_text = await self._read_page_text(page)
                title = (await page.title()).lower()
                if any(marker in title or marker in page_text for marker in _VERIFICATION_MARKERS):
                    if not saw_verification_page:
                        logger.info("检测到验证页，等待自动跳转: %s", page.url)
                        saw_verification_page = True
                elif saw_verification_page:
                    logger.info("验证页已跳转，当前 URL: %s", page.url)
                    saw_verification_page = False
            except Exception:
                # 页面正在导航中（execution context destroyed），等待导航完成
                logger.debug("页面正在导航中，等待...")
                try:
                    await page.wait_for_load_state("load", timeout=10000)
                except Exception:
                    pass

            await asyncio.sleep(1)

        return await self._has_tweets(page)

    async def _has_tweets(self, page) -> bool:
        try:
            for selector in _TWEET_SELECTORS:
                if await page.query_selector(selector):
                    return True
        except Exception:
            pass
        return False

    async def _read_page_text(self, page) -> str:
        try:
            body = await page.query_selector("body")
            if not body:
                return ""
            return (await body.inner_text()).lower()
        except Exception:
            return ""

    async def _scrape_tweets(self, page, target: int) -> List[Dict[str, Any]]:
        posts: List[Dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        max_pages = (target // 15) + 5  # Nitter 每页约 20 条，留足余量

        for round_num in range(max_pages):
            elements = await self._query_tweet_elements(page)
            logger.info(f"第 {round_num + 1} 轮: 页面 {len(elements)} 条, 已收集 {len(posts)}/{target}")

            for el in elements:
                try:
                    post = await self._extract(el)
                    key = (post["text"], post["created_at"])
                    if post["text"] and key not in seen:
                        seen.add(key)
                        posts.append(post)
                        if len(posts) >= target:
                            return posts
                except Exception:
                    continue

            if not await self._load_more(page):
                break

        return posts

    async def _query_tweet_elements(self, page):
        for selector in _TWEET_SELECTORS:
            elements = await page.query_selector_all(selector)
            if elements:
                return elements
        return []

    async def _extract(self, el) -> Dict[str, str]:
        text_el = await el.query_selector(".tweet-content")
        text = (await text_el.inner_text()).strip() if text_el else ""
        time_el = await el.query_selector(".tweet-date a")
        created_at = ""
        if time_el:
            created_at = await time_el.get_attribute("title") or await time_el.inner_text()
        return {"text": text, "created_at": created_at}

    async def _load_more(self, page) -> bool:
        """点击 Nitter 的 'Show more' 翻页链接，等待新页面加载完成。"""
        try:
            # Nitter "Show more" 通常是 .show-more a（一个链接，点击后导航到新页面）
            show_more = await page.query_selector(
                ".show-more:not(.timeline-item) a, .timeline-footer .show-more a"
            )
            if not show_more or not await show_more.is_visible():
                # 退而求其次：尝试找 .show-more 按钮本身
                show_more = await page.query_selector(
                    ".show-more:not(.timeline-item), .timeline-footer .show-more"
                )
            if show_more and await show_more.is_visible():
                old_url = page.url
                await show_more.click()
                # Nitter 翻页是页面导航，等待新页面加载
                try:
                    await page.wait_for_load_state("load", timeout=30000)
                except Exception:
                    pass
                # 额外等待推文元素出现
                for _ in range(10):
                    if await self._has_tweets(page):
                        return True
                    await asyncio.sleep(1)
                # URL 变了说明确实翻页了，即使暂时没推文也继续
                return page.url != old_url

            # 无 show-more 按钮，尝试滚动
            old = len(await self._query_tweet_elements(page))
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            return len(await self._query_tweet_elements(page)) > old
        except Exception as e:
            logger.debug(f"_load_more 异常: {e}")
            return False

    # ---------- 同步入口 ----------

    def get_tweets(self, username: str, count: int = 10) -> List[Dict[str, Any]]:
        """同步接口，自动适配 Streamlit 等已有 event loop 的环境"""
        try:
            try:
                asyncio.get_running_loop()
                # 已有 loop（Streamlit），在新线程中 asyncio.run
                with ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, self._async_get_tweets(username, count)).result(timeout=180)
            except RuntimeError:
                return asyncio.run(self._async_get_tweets(username, count))
        except Exception as e:
            logger.error(f"抓取失败: {e}")
            logger.debug("抓取失败详细堆栈", exc_info=True)
            return _ERROR(f"Failed to fetch posts - {e}")
