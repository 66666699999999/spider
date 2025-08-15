from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Task as DBTask
from app.schemas.task import TaskCreate, TaskResponse
from app.services.task_logic_service import TaskLogicService
from app.services.task_service import get_running_tasks

# 创建定时任务路由器
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/running", response_model=List[Dict[str, Any]])
async def get_running_tasks_endpoint():
    """获取正在运行的定时任务

    Returns:
        正在运行的任务列表
    """
    return get_running_tasks()


# 同时支持带和不带斜杠的URL格式
@router.get("/")
@router.get("", include_in_schema=False)
async def list_tasks(db: Session = Depends(get_db)) -> List[Task]:
    """获取所有定时任务列表"""
    tasks = await TaskLogicService.get_all_tasks(db)
    return tasks


# 同时支持带和不带斜杠的URL格式
@router.post("/", response_model=TaskResponse)
@router.post("", include_in_schema=False)
async def create_task(
    task: TaskCreate = Body(...), db: Session = Depends(get_db)
) -> TaskResponse:
    """创建新的定时任务

    Args:
        task: 任务创建请求体，包含spider_id、cron_expression和description
        db: 数据库会话

    Returns:
        创建的任务信息
    """
    # 验证cron表达式
    if not TaskLogicService.validate_cron_expression(task.cron_expression):
        raise HTTPException(
            detail="Invalid cron expression. Format: 'minute hour day month day_of_week'",
            status_code=400,
        )

    try:
        return await TaskLogicService.create_new_task(task, db)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Failed to schedule task: {str(e)}", status_code=500
        )


@router.get("/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    """获取指定ID的定时任务"""
    task = await TaskLogicService.get_task_by_id(task_id, db)
    if not task:
        raise HTTPException(detail="Task not found", status_code=404)
    return task


@router.delete("/{task_id}", response_model=Dict[str, Any])
async def delete_task(task_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """删除定时任务

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        删除结果
    """
    try:
        return await TaskLogicService.delete_existing_task(task_id, db)
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=404)
    except Exception as e:
        db.rollback()
        raise HTTPException(detail=f"Failed to delete task: {str(e)}", status_code=500)
