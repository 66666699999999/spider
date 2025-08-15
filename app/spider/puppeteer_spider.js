const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const toml = require('toml');

class PuppeteerSpider {
    constructor() {
        this.config = this.loadConfig();
        this.scriptPath = path.join(__dirname, 'puppeteer_script.js');
        // 确保脚本文件存在
        if (!fs.existsSync(this.scriptPath)) {
            this.createDefaultScript();
        }
    }

    loadConfig() {
        // 读取配置文件
        try {
            const configPath = path.join(__dirname, '..', 'config', 'config.toml');
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

    createDefaultScript() {
        /**创建默认的Puppeteer脚本**/
        const scriptContent = `const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function run(url, outputDir) {
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
        await page.waitForTimeout(3000);

        // 截取页面截图
        const timestamp = Date.now();
        const screenshotPath = path.join(outputDir, \`\${timestamp}.png\`);
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
        console.error('Error in Puppeteer script:', error);
        return {
            status: 'error',
            message: error.message
        };
    }
}

// 从命令行参数获取URL和输出目录
const args = process.argv.slice(2);
const url = args[0];
const outputDir = args[1];

// 运行爬虫并输出结果
run(url, outputDir)
    .then(result => {
        console.log(JSON.stringify(result));
    })
    .catch(error => {
        console.error(JSON.stringify({
            status: 'error',
            message: error.message
        }));
    });`;

        fs.writeFileSync(this.scriptPath, scriptContent, 'utf-8');
        console.log(`Default Puppeteer script created at ${this.scriptPath}`);
    }

    async run(url) {
        if (!url) {
            throw new Error('URL is required');
        }

        try {
            // 获取输出目录
            const rootPath = path.join(__dirname, '..', '..');
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
            await page.waitForTimeout(3000);

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
async function main(url) {
    const spider = new PuppeteerSpider();
    const result = await spider.run(url);
    console.log(result);
}

// 如果直接运行此脚本
if (require.main === module) {
    const args = process.argv.slice(2);
    const url = args[0];
    if (url) {
        main(url);
    } else {
        console.error('URL is required');
        process.exit(1);
    }
}

module.exports = { PuppeteerSpider, main };