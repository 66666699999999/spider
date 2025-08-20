import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Playwright, async_playwright, expect

from app.config.load_config import Config


class ScreenShotSpider:
    def __init__(self):
        self.config = Config()

    def load_cookie(self) -> List[Dict[str, Any]]:
        cookie_path = (
            self.config.BASE_DIR / "public" / "cookie" / "x.com_json_1755533995907.json"
        )

        try:
            with open(cookie_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            # 规范化sameSite值
            for cookie in cookies:
                if "sameSite" in cookie:
                    cookie["sameSite"] = {
                        "strict": "Strict",
                        "lax": "Lax",
                        "none": "None",
                    }.get(cookie["sameSite"].lower(), None)
                    if cookie["sameSite"] is None:
                        del cookie["sameSite"]
            return cookies
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return []

    async def run(self, url: Optional[str] = None) -> Dict[str, Any]:
        """运行爬虫，返回结果"""
        if not url:
            raise ValueError("URL is required")

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=False)
                context = await browser.new_context()

                cookies = await asyncio.to_thread(self.load_cookie)
                if cookies:
                    await context.add_cookies(cookies)

                page = await context.new_page()
                await page.goto(url)

                # 等待文章元素可见
                await expect(page.locator("article").nth(0)).to_be_visible(
                    timeout=200000
                )
                count = await page.locator("article").count()
                print(f"Found {count} articles")

                # 移除第一个article的祖先元素
                # 将推主的article删除，截图第一个评论
                article = page.locator("article").first
                await article.locator("xpath=../../..").first.evaluate(
                    "(element) => element.remove()"
                )

                # 截取目标article的截图
                target = page.locator("article").first
                screenshot_dir = self.config.BASE_DIR / "public" / "pic"

                screenshot_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = screenshot_dir / f"{int(time.time())}.png"
                await target.screenshot(path=str(screenshot_path), type="png")
                print(f"Screenshot saved to {screenshot_path}")

                # 确保浏览器和上下文被关闭
                await context.close()
                await browser.close()

                return {
                    "status": "success",
                    "message": "Screenshot captured successfully",
                    "screenshot_path": str(screenshot_path),
                }
        except Exception as e:
            print(f"Error in run function: {e}")
            return {"status": "error", "message": str(e)}


# 为了保持向后兼容性，保留main函数
async def main(url: str) -> None:
    spider = ScreenShotSpider()
    await spider.run(url)


if __name__ == "__main__":
    asyncio.run(main("https://x.com/leeoxiang/status/1778304537973203120"))
