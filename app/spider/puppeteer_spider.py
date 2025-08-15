import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

import asyncio
from app.config.load_config import Config


class PuppeteerSpider:
    def __init__(self):
        self.config = Config()
        self.config_data = self.config.load_file()
        # 获取 Node.js 脚本路径
        self.script_path = Path(__file__).parent / "puppeteer_script.js"
        # 确保脚本文件存在
        if not self.script_path.exists():
            self._create_default_script()

    def _create_default_script(self):
        """创建默认的 Puppeteer 脚本"""
        script_content = """
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function run(url, outputDir) {
    try {
        // 启动浏览器
        const browser = await puppeteer.launch({
            headless: false,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        // 创建新页面
        const page = await browser.newPage();

        // 导航到目标 URL
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
        console.error('Error in Puppeteer script:', error);
        return {
            status: 'error',
            message: error.message
        };
    }
}

// 从命令行参数获取 URL 和输出目录
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
    });
        """
        with open(self.script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print(f"Default Puppeteer script created at {self.script_path}")

    def _get_node_path(self):
        """获取 Node.js 可执行文件路径"""
        # 尝试从环境变量获取 Node.js 路径
        node_path = os.environ.get('NODE_PATH')
        if node_path and os.path.exists(node_path):
            return node_path

        # 尝试标准安装路径
        if os.name == 'nt':  # Windows
            standard_paths = [
                'C:\\Program Files\\nodejs\\node.exe',
                'C:\\Program Files (x86)\\nodejs\\node.exe',
            ]
        else:  # Unix-like
            standard_paths = ['/usr/bin/node', '/usr/local/bin/node']

        for path in standard_paths:
            if os.path.exists(path):
                return path

        raise ValueError("Node.js not found. Please install Node.js or set NODE_PATH environment variable.")

    async def run(self, url: Optional[str] = None) -> Dict[str, Any]:
        """运行 Puppeteer 爬虫"""
        if not url:
            raise ValueError("URL is required")

        try:
            # 获取输出目录
            output_dir = self.config.ROOT_PATH / self.config_data.get("paths", {}).get("puppeteer_screenshot", "screenshots/puppeteer")
            output_dir.mkdir(parents=True, exist_ok=True)

            # 获取 Node.js 路径
            node_path = await asyncio.to_thread(self._get_node_path)

            # 构造命令
            command = [
                node_path,
                str(self.script_path),
                url,
                str(output_dir)
            ]

            print(f"Running command: {' '.join(command)}")

            # 运行命令
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 获取输出
            stdout, stderr = await process.communicate()

            # 解析输出
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace').strip()
                print(f"Error running Puppeteer script: {error_msg}")
                return {
                    "status": "error",
                    "message": f"Puppeteer script failed with error: {error_msg}"
                }

            # 解析标准输出
            result_str = stdout.decode('utf-8', errors='replace').strip()
            try:
                result = json.loads(result_str)
                return result
            except json.JSONDecodeError:
                print(f"Failed to parse Puppeteer script output: {result_str}")
                return {
                    "status": "error",
                    "message": f"Failed to parse Puppeteer script output: {result_str}"
                }

        except Exception as e:
            print(f"Error in PuppeteerSpider.run: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# 为了保持向后兼容性，保留main函数
async def main(url: str) -> None:
    spider = PuppeteerSpider()
    result = await spider.run(url)
    print(result)