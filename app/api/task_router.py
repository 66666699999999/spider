from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.database import get_db
from app.database.models import Task as DBTask
from app.services.task_service import schedule_task, remove_task

# 创建定时任务路由器
router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    url: str
    cron_expression: str
    description: str = ""


class Task(BaseModel):
    id: int
    url: str
    cron_expression: str
    description: str
    created_at: datetime
    job_id: str = ""

    class Config:
        orm_mode = True


@router.get("/")
async def list_tasks(db: Session = Depends(get_db)) -> List[Task]:
    """获取所有定时任务列表"""
    tasks = db.query(DBTask).all()
    return tasks


@router.post("/")
async def create_task(task: TaskCreate = Body(...), db: Session = Depends(get_db)) -> Task:
    """创建新的定时任务"""
    # 验证cron表达式 (简单验证)
    if not task.cron_expression or len(task.cron_expression.split()) != 5:
        raise HTTPException(
            detail="Invalid cron expression. Format: 'minute hour day month day_of_week'",
            status_code=400
        )

    try:
        # 创建数据库任务对象
        db_task = DBTask(
            url=task.url,
            cron_expression=task.cron_expression,
            description=task.description
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        # 安排定时任务
        schedule_result = await schedule_task(
            task_id=db_task.id,
            url=db_task.url,
            cron_expression=db_task.cron_expression
        )
        db_task.job_id = schedule_result["job_id"]
        db.commit()

        return db_task
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Failed to schedule task: {str(e)}",
            status_code=500
        )


@router.get("/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    """获取指定ID的定时任务"""
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(detail="Task not found", status_code=404)
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    """删除指定ID的定时任务"""
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(detail="Task not found", status_code=404)

    try:
        # 从调度器中移除任务
        await remove_task(task_id)
        # 从数据库中删除
        db.delete(task)
        db.commit()
        return {"message": "Task deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Failed to delete task: {str(e)}",
            status_code=500
        )