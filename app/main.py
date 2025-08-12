from fastapi import FastAPI
from app.api.router import router
from app.api.task_router import router as task_router
import uvicorn
import os
from pathlib import Path

# 数据库初始化
from app.database.database import engine
from app.database.models import Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

FILE = Path(__file__).resolve()
project_root = FILE.parents[1]

app = FastAPI(title="Auto work API")
app.include_router(router)
app.include_router(task_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")