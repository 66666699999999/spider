import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from playwright.async_api import Playwright, async_playwright, expect
from app.config.load_config import Config

config = Config()
config_data = config.load_file()


def load_cookie() -> List[Dict[str, Any]]:
    cookie_path = config.ROOT_PATH / config_data["paths"]["cookie"]
    try:
        with open(cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        # 规范化sameSite值
        for cookie in cookies:
            if "sameSite" in cookie:
                cookie["sameSite"] = {
                    "strict": "Strict",
                    "lax": "Lax",
                    "none": "None"
                }.get(cookie["sameSite"].lower(), None)
                if cookie["sameSite"] is None:
                    del cookie["sameSite"]
        return cookies
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return []


async def run(playwright: Playwright, url: str) -> None:
    try:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()

        cookies = await asyncio.to_thread(load_cookie)
        if cookies:
            await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto(url)

        # 等待文章元素可见
        
        await expect(page.locator('article').nth(0)).to_be_visible(timeout=200000)
        count = await page.locator("article").count()
        print(f"Found {count} articles")

        # 移除第一个article的祖先元素
        # 将推主的article删除，截图第一个评论
        article = page.locator("article").first
        await article.locator("xpath=../../..").first.evaluate("(element) => element.remove()")

        # 截取目标article的截图
        target = page.locator("article").first
        screenshot_dir = config.ROOT_PATH / config_data["paths"]["screenshot"]
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / f"{int(time.time())}.png"
        await target.screenshot(path=str(screenshot_path), type="png")
        print(f"Screenshot saved to {screenshot_path}")

    except Exception as e:
        print(f"Error in run function: {e}")
    finally:
        # 确保浏览器和上下文被关闭
        if 'context' in locals():
            await context.close()
        if 'browser' in locals():
            await browser.close()


async def main(url: str) -> None:
    async with async_playwright() as playwright:
        await run(playwright, url)
