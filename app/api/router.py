from fastapi import FastAPI

from app.api.spider_router import router as spider_router
from app.api.task_router import router as task_router
from app.database.database_ssh import lifespan_manager

# 使用database.py中的lifespan_manager
app = FastAPI(title="Auto work API", lifespan=lifespan_manager)

app.include_router(task_router)
app.include_router(spider_router)
