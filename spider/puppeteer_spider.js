import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import toml from 'toml';

class PuppeteerSpider {
    constructor() {
        this.config = this.loadConfig();
    }

    loadConfig() {
        // 读取配置文件
        try {
            const configPath = path.join(path.dirname(import.meta.url).replace('file:///', ''), '..', 'config', 'config.toml');
            const configContent = fs.readFileSync(configPath, 'utf-8');
            return toml.parse(configContent);
        } catch (error) {
            console.error('Failed to load config:', error);
            // 返回默认配置
            return {
                paths: {
                    puppeteer_screenshot: 'screenshots/puppeteer'
                }
            };
        }
    }

    async run(url) {
        if (!url) {
            throw new Error('URL is required');
        }

        try {
            // 获取输出目录
            const rootPath = path.join(path.dirname(import.meta.url).replace('file:///', ''), '..');
            const outputDir = path.join(rootPath, this.config.paths?.puppeteer_screenshot || 'screenshots/puppeteer');

            // 确保输出目录存在
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }

            // 直接调用Puppeteer函数
            return await this.executePuppeteer(url, outputDir);
        } catch (error) {
            console.error(`Error in PuppeteerSpider.run: ${error}`);
            return {
                status: 'error',
                message: error.message
            };
        }
    }

    async executePuppeteer(url, outputDir) {
        try {
            // 启动浏览器
            const browser = await puppeteer.launch({
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });

            // 创建新页面
            const page = await browser.newPage();

            // 导航到目标URL
            await page.goto(url, { waitUntil: 'networkidle2' });

            // 等待页面加载完成
            await page.waitForSelector('article', { timeout: 3000 });

            // 截取页面截图
            const timestamp = Date.now();
            const screenshotPath = path.join(outputDir, `${timestamp}.png`);
            await page.screenshot({ path: screenshotPath, fullPage: true });

            // 获取页面标题
            const title = await page.title();

            // 关闭浏览器
            await browser.close();

            return {
                status: 'success',
                message: 'Puppeteer spider ran successfully',
                title: title,
                screenshotPath: screenshotPath
            };
        } catch (error) {
            console.error('Error in Puppeteer execution:', error);
            return {
                status: 'error',
                message: error.message
            };
        }
    }
}

// 为了保持向后兼容性，保留main函数
export async function main(url) {
    const spider = new PuppeteerSpider();
    const result = await spider.run(url);
    console.log(result);
}

// 如果直接运行此脚本
if (import.meta.main) {
    const args = process.argv.slice(2);
    const url = args[0];
    if (url) {
        main(url);
    } else {
        console.error('URL is required');
        process.exit(1);
    }
}

export { PuppeteerSpider, main };