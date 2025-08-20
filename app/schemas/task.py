from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    spider_id: int = Field(..., example=1)
    cron_expression: str = Field(..., example="0 0 * * *")
    description: Optional[str] = Field(None, example="每日运行爬虫")


class TaskCreate(TaskBase):
    pass


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    spider_id: int
    cron_expression: str
    description: Optional[str] = None
    created_at: datetime
    job_id: Optional[str] = ""

    class Config:
        from_attributes = True
