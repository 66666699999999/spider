import importlib
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.load_config import Config
from app.database.models import Spider
from app.schemas.spider import SpiderCreate, SpiderUpdate

logger = logging.getLogger(__name__)


class SpiderLogicService:
    @staticmethod
    async def run_spider(spider_id: int, db: AsyncSession) -> Dict[str, Any]:
        """运行指定ID的爬虫"""
        # 获取爬虫信息
        spider = await db.get(Spider, spider_id)
        if not spider:
            raise ValueError(f"Spider with id {spider_id} not found")

        if not spider.is_active:
            raise ValueError(f"Spider {spider_id} is not active")

        # 根据爬虫语言类型选择不同的执行方式
        try:
            if spider.language == 'python':
                result = await cls._run_python_spider(spider)
            elif spider.language == 'javascript':
                result = await cls._run_javascript_spider(spider)
            else:
                raise ValueError(f"Unsupported spider language: {spider.language}")

            logger.info(f"Spider {spider_id} ({spider.name}) run successfully")
            return {
                "status": "success",
                "message": f"Spider {spider_id} ({spider.name}) run successfully",
                "result": result,
            }
        except Exception as e:
            logger.error(f"Error running spider {spider_id} ({spider.name}): {e}")
            raise ValueError(f"Error running spider: {e}")

    @staticmethod
    async def _run_python_spider(spider: Spider) -> Dict[str, Any]:
        """运行Python爬虫"""
        try:
            # 动态导入爬虫模块
            import importlib
            module = importlib.import_module(spider.module_path)
            # 获取爬虫类
            spider_class = getattr(module, spider.class_name)
            # 实例化爬虫
            spider_instance = spider_class()
            # 运行爬虫
            result = await spider_instance.run()
            return result
        except ImportError as e:
            logger.error(f"Failed to import spider module {spider.module_path}: {e}")
            raise ValueError(f"Failed to import spider module: {e}")
        except AttributeError as e:
            logger.error(
                f"Failed to find spider class {spider.class_name} in module {spider.module_path}: {e}"
            )
            raise ValueError(f"Failed to find spider class: {e}")

    @staticmethod
    async def _run_javascript_spider(spider: Spider) -> Dict[str, Any]:
        """运行JavaScript爬虫"""
        try:
            config = Config()
            config_data = config.load_file()

            # 获取Node.js路径
            node_path = cls._get_node_path()

            # 构造命令
            command = [
                node_path,
                spider.module_path,
                spider.class_name  # 这里class_name用作入口函数名
            ]

            logger.info(f"Running JavaScript spider command: {' '.join(command)}")

            # 运行命令
            process = await subprocess.create_subprocess_exec(
                *command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 获取输出
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace').strip()
                logger.error(f"JavaScript spider error: {error_msg}")
                raise ValueError(f"JavaScript spider failed: {error_msg}")

            # 解析输出
            result_str = stdout.decode('utf-8', errors='replace').strip()
            try:
                import json
                result = json.loads(result_str)
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JavaScript spider output: {result_str}")
                raise ValueError(f"Failed to parse JavaScript spider output")
        except Exception as e:
            logger.error(f"Error running JavaScript spider: {e}")
            raise ValueError(f"Error running JavaScript spider: {e}")

    @staticmethod
    def _get_node_path() -> str:
        """获取Node.js可执行文件路径"""
        # 尝试从环境变量获取
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

    @staticmethod
    async def get_spider_by_id(spider_id: int, db: AsyncSession) -> Spider:
        """根据ID获取爬虫"""
        spider = await db.get(Spider, spider_id)
        if not spider:
            raise ValueError(f"Spider with id {spider_id} not found")
        return spider

    @staticmethod
    async def get_all_spiders(db: AsyncSession) -> List[Spider]:
        """获取所有爬虫"""
        result = await db.execute(select(Spider))
        return result.scalars().all()

    @staticmethod
    async def create_spider(spider_data: SpiderCreate, db: AsyncSession) -> Spider:
        """创建新爬虫"""
        # 检查爬虫名称是否已存在
        result = await db.execute(select(Spider).where(Spider.name == spider_data.name))
        existing_spider = result.scalars().first()

        if existing_spider:
            raise ValueError(f"Spider with name '{spider_data.name}' already exists")

        # 设置默认语言为Python
        language = spider_data.language if hasattr(spider_data, 'language') else 'python'

        # 创建新爬虫
        db_spider = Spider(
            name=spider_data.name,
            description=spider_data.description,
            module_path=spider_data.module_path,
            class_name=spider_data.class_name,
            is_active=spider_data.is_active,
            language=language,
        )

        db.add(db_spider)
        await db.commit()
        await db.refresh(db_spider)

        logger.info(f"Spider {db_spider.id} ({db_spider.name}) created successfully")
        return db_spider

    @staticmethod
    async def update_spider(
        spider_id: int, spider_data: SpiderUpdate, db: AsyncSession
    ) -> Spider:
        """更新爬虫信息"""
        db_spider = await db.get(Spider, spider_id)
        if not db_spider:
            raise ValueError(f"Spider with id {spider_id} not found")

        # 更新爬虫信息
        for key, value in spider_data.dict(exclude_unset=True).items():
            setattr(db_spider, key, value)

        db.add(db_spider)
        await db.commit()
        await db.refresh(db_spider)

        logger.info(f"Spider {spider_id} ({db_spider.name}) updated successfully")
        return db_spider

    @staticmethod
    async def delete_spider(spider_id: int, db: AsyncSession) -> None:
        """删除爬虫"""
        spider = await db.get(Spider, spider_id)
        if not spider:
            raise ValueError(f"Spider with id {spider_id} not found")

        await db.delete(spider)
        await db.commit()

        logger.info(f"Spider {spider_id} ({spider.name}) deleted successfully")
