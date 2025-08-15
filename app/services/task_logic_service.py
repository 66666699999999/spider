# app/services/task_logic_service.py
import logging
from typing import Any, Dict, List

# --- SQLAlchemy 2.0 导入 ---
from sqlalchemy import delete, select  # 导入 select 和 delete
from sqlalchemy.ext.asyncio import AsyncSession  # 导入 AsyncSession 类型提示

# --- 内部导入 ---
from app.database.models import Task as DBTask  # 确保模型导入正确
from app.schemas.task import TaskCreate  # 确保 Pydantic 模型导入正确
from app.services.task_service import remove_task, schedule_task  # 确保调度服务导入正确

# --- 配置 ---
logger = logging.getLogger(__name__)


class TaskLogicService:
    @staticmethod
    def validate_cron_expression(cron_expression: str) -> bool:
        """验证cron表达式格式 (这个方法不涉及数据库，可以保持不变)"""
        if not cron_expression or len(cron_expression.split()) != 5:
            return False
        return True

    # --- 修改 1: 类型提示 + SQLAlchemy 2.0 语法 ---
    @staticmethod
    async def get_all_tasks(db: AsyncSession) -> List[DBTask]:
        """获取所有任务"""
        # 使用 select() 和 await execute()
        stmt = select(DBTask)
        result = await db.execute(stmt)
        # 使用 scalars().all() 获取 ORM 对象列表
        tasks = result.scalars().all()
        return tasks

    # --- 修改 2: 类型提示 + SQLAlchemy 2.0 语法 ---
    @staticmethod
    async def get_task_by_id(
        task_id: int, db: AsyncSession
    ) -> DBTask | None:  # 添加 | None 返回类型提示更准确
        """根据ID获取任务"""
        # 使用 select() + filter (where) + await execute()
        stmt = select(DBTask).where(DBTask.id == task_id)
        result = await db.execute(stmt)
        # 使用 scalars().first() 获取单个 ORM 对象或 None
        task = result.scalars().first()
        return task

    # --- 修改 3: async def + await + SQLAlchemy 2.0 语法 ---
    @staticmethod
    async def create_new_task(task: TaskCreate, db: AsyncSession) -> DBTask:
        """创建新任务"""
        # 1. 创建数据库任务对象 (这一步是同步的)
        db_task = DBTask(
            url=task.url,
            cron_expression=task.cron_expression,
            description=task.description,
        )
        # 2. 添加到会话 (同步)
        db.add(db_task)
        # 3. 提交到数据库 (异步，需要 await)
        await db.commit()
        # 4. 刷新对象以获取自动生成的 ID (异步，需要 await)
        await db.refresh(db_task)

        try:
            # 5. 安排定时任务 (异步，需要 await)
            schedule_result = await schedule_task(
                task_id=db_task.id,
                url=db_task.url,
                cron_expression=db_task.cron_expression,
            )
            # 6. 更新数据库中的 job_id (如果需要的话)
            #    注意：通常 job_id 不应该存储在数据库中，因为重启后会丢失。
            #    更好的方式是在应用启动时根据数据库中的任务重新调度。
            #    这里假设你的模型中有 job_id 字段。
            # db_task.job_id = schedule_result["job_id"] # 如果模型有此字段
            # await db.commit() # 如果更新了 db_task，需要再次提交

            logger.info(
                f"Task {db_task.id} scheduled with job ID {schedule_result.get('job_id')}"
            )
        except Exception as e:
            logger.error(f"Failed to schedule task {db_task.id}: {e}")
            # 可选：如果调度失败，可以选择回滚数据库操作
            # await db.rollback()
            # raise # 重新抛出异常

        # 7. 返回创建好的任务对象
        return db_task

    # --- 修改 4: async def + await + SQLAlchemy 2.0 语法 ---
    @staticmethod
    async def delete_existing_task(task_id: int, db: AsyncSession) -> Dict[str, str]:
        """删除任务"""
        # 1. 先查找任务 (使用新的查询语法)
        task = await TaskLogicService.get_task_by_id(task_id, db)
        if not task:
            # 更好的做法是抛出自定义异常或 HTTPException，让路由处理
            raise ValueError("Task not found")

        try:
            # 2. 从调度器中移除任务 (异步，需要 await)
            await remove_task(task_id)
            logger.info(f"Task {task_id} removed from scheduler.")
        except Exception as e:
            logger.error(f"Failed to remove task {task_id} from scheduler: {e}")
            # 根据业务逻辑决定是否继续删除数据库记录
            # 这里我们选择继续删除数据库记录

        # 3. 从数据库中删除 (使用 delete 构造函数)
        stmt = delete(DBTask).where(DBTask.id == task_id)
        await db.execute(stmt)
        # 4. 提交事务 (异步，需要 await)
        await db.commit()

        logger.info(f"Task {task_id} deleted from database.")
        return {"message": "Task deleted successfully"}
