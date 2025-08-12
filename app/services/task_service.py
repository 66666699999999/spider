import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.screen_shot_service import main
from typing import Dict, Any
import logging

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


async def schedule_task(task_id: int, url: str, cron_expression: str) -> Dict[str, Any]:
    """安排定时任务"""
    # 解析cron表达式
    cron_parts = cron_expression.split()
    if len(cron_parts) != 5:
        raise ValueError("Invalid cron expression. Format: 'minute hour day month day_of_week'")

    minute, hour, day, month, day_of_week = cron_parts

    # 创建触发器
    trigger = CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week
    )

    # 添加任务到调度器
    job_id = f"task_{task_id}"
    scheduler.add_job(
        func=lambda: asyncio.create_task(main(url)),
        trigger=trigger,
        id=job_id,
        name=f"Screenshot task for {url}",
        replace_existing=True
    )

    logger.info(f"Task {task_id} scheduled with cron expression: {cron_expression}")

    return {
        "job_id": job_id,
        "message": f"Task {task_id} scheduled successfully"
    }


async def remove_task(task_id: int) -> Dict[str, Any]:
    """移除定时任务"""
    job_id = f"task_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Task {task_id} removed")
        return {
            "message": f"Task {task_id} removed successfully"
        }
    else:
        raise ValueError(f"Task {task_id} not found in scheduler")


# 启动调度器
start_scheduler()