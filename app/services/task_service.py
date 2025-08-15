import asyncio
import logging
from typing import Any, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.spider.screen_shot_service import main

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
        func=lambda: asyncio.create_task(main(url)),
        trigger=trigger,
        id=job_id,
        name=f"Screenshot task for {url}",
        replace_existing=True,
    )

    logger.info(f"Task {task_id} scheduled with cron expression: {cron_expression}")

    return {"job_id": job_id, "message": f"Task {task_id} scheduled successfully"}


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
