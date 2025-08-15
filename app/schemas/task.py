from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


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
    job_id: Optional[str] = ""

    class Config:
        from_attributes = True
