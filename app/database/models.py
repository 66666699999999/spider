from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.database.database import Base


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Spider(BaseModel):
    __tablename__ = "spiders"

    name = Column(String, unique=True, index=True)
    description = Column(String)
    module_path = Column(String)
    class_name = Column(String)
    is_active = Column(Boolean, default=True)
    language = Column(String, default='python')

    tasks = relationship("Task", back_populates="spider")


class SpiderTarget(BaseModel):
    __tablename__ = "spider_targets"

    spider_name = Column(String, index=True)
    url = Column(String)


class Task(BaseModel):
    __tablename__ = "tasks"

    spider_id = Column(Integer, ForeignKey("spiders.id"), index=True)
    description = Column(String, index=True)
    url = Column(String)
    cron_expression = Column(String)
    job_id = Column(String, nullable=True)

    spider = relationship("Spider", back_populates="tasks")
