import asyncio
import json
import time
from playwright.async_api import Playwright, async_playwright, expect
from app.config.load_config import Config

config = Config()
child_path = config.load_file()

def load_cookie():
    path = config.ROOT_PATH / child_path["paths"]["cookie"]
    with open(path, "r", encoding="utf-8") as f:
        cookies = json.load(f)

        # 如果没有指定或指定错误的 sameSite 则删除 sameSite 元素
        for cookie in cookies:
            cookie['sameSite'] = {'strict': 'Strict', 'Lax': 'lax', 'none': 'None'}.get(cookie['sameSite'])
            if cookie['sameSite'] not in ['strict', 'lax', 'none']:
                del cookie['sameSite']
    return cookies


async def run(playwright: Playwright, url) -> None:
    browser =  await playwright.chromium.launch(headless=False)
    context =  await browser.new_context()

    cookies =  await asyncio.to_thread(load_cookie)
    await context.add_cookies(cookies)

    page =  await context.new_page()
    await page.goto(url)
    try:
        await expect(page.locator('article').nth(0)).to_be_visible(timeout=200000)
        count =  await page.locator("article").count()
        article = page.locator("article").first
        await article.locator("xpath=../../..").first.evaluate("(element) => element.remove()")
        target = page.locator("article").first
        path = config.ROOT_PATH / child_path["paths"]["screenshot"] / f"{time.time():.0f}.png"
        await target.screenshot(path=path, type="png")
    except Exception as e:
        print(e)

    # ---------------------
    await context.close()
    await browser.close()


async def main(url) -> None:
    async with async_playwright() as playwright:
        await run(playwright, url)
