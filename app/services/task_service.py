import asyncio
import json
import logging
import os
import subprocess
from typing import Any, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config.load_config import Config
from app.database.database import db_manager
from app.database.models import Spider
from app.services.spider_logic_service import SpiderLogicService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建调度器
scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """启动调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")


async def schedule_task(
    task_id: int, spider_id: int, cron_expression: str
) -> Dict[str, Any]:
    """安排定时任务

    Args:
        task_id: 任务ID
        spider_id: 爬虫ID
        cron_expression: cron表达式

    Returns:
        任务调度结果
    """
    # 解析cron表达式
    cron_parts = cron_expression.split()
    if len(cron_parts) != 5:
        raise ValueError(
            "Invalid cron expression. Format: 'minute hour day month day_of_week'"
        )

    minute, hour, day, month, day_of_week = cron_parts

    # 创建触发器
    trigger = CronTrigger(
        minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
    )

    # 添加任务到调度器
    job_id = f"task_{task_id}"
    scheduler.add_job(
        func=run_spider_wrapper,
        trigger=trigger,
        id=job_id,
        name=f"Task for spider {spider_id}",
        replace_existing=True,
        args=[spider_id],
    )

    logger.info(
        f"Task {task_id} scheduled with cron expression: {cron_expression} for spider {spider_id}"
    )

    return {"job_id": job_id, "message": f"Task {task_id} scheduled successfully"}


# 创建包装函数来处理异步调用
async def run_spider_wrapper(spider_id: int) -> Dict[str, Any]:
    """包装函数，用于在调度器中运行异步爬虫"""
    try:
        return await run_spider_by_id(spider_id)
    except Exception as e:
        logger.error(f"Error in scheduled task for spider {spider_id}: {str(e)}")
        return {"status": "error", "message": f"Error running spider: {str(e)}"}


async def run_spider_by_id(spider_id: int) -> Dict[str, Any]:
    """根据爬虫ID运行爬虫"""
    try:
        # 获取数据库会话
        session_gennerator = db_manager.get_db()
        db_session = await anext(session_gennerator)

        # 运行爬虫
        result = await SpiderLogicService.run_spider(spider_id, db_session)
        logger.info(f"Scheduled run of spider {spider_id} completed successfully")

        # 提交事务
        try:
            await anext(session_gennerator)
        except StopAsyncIteration:
            pass

        return result
    except Exception as e:
        logger.error(
            f"Error running spider {spider_id} in scheduled task: {str(e)}",
            exc_info=True,
        )
        return {"status": "error", "message": f"Error running spider: {str(e)}"}


async def remove_task(task_id: int) -> Dict[str, Any]:
    """移除定时任务"""
    job_id = f"task_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Task {task_id} removed")
        return {"message": f"Task {task_id} removed successfully"}
    else:
        raise ValueError(f"Task {task_id} not found in scheduler")


def get_running_tasks() -> Dict[str, Any]:
    """获取所有正在运行的定时任务"""
    jobs = scheduler.get_jobs()
    running_tasks = []

    for job in jobs:
        # 提取任务ID (从job_id格式 "task_{task_id}" 中提取)
        if job.id.startswith("task_"):
            try:
                task_id = int(job.id[5:])  # 去掉前缀 "task_"
                running_tasks.append(
                    {
                        "task_id": task_id,
                        "job_id": job.id,
                        "name": job.name,
                        "next_run_time": str(job.next_run_time),
                        "trigger": str(job.trigger),
                    }
                )
            except ValueError:
                # 如果无法提取task_id，跳过这个任务
                continue

    return {"total_tasks": len(running_tasks), "tasks": running_tasks}


# 启动调度器
start_scheduler()
