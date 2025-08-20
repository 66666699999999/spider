from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SpiderBase(BaseModel):
    name: str = Field(..., description="爬虫名称")
    description: Optional[str] = Field(None, description="爬虫描述")
    module_path: str = Field(..., description="爬虫模块路径")
    class_name: str = Field(..., description="爬虫类名")
    is_active: bool = Field(True, description="是否激活")
    language: str = Field(
        "python", description="爬虫语言类型，支持 'python' 和 'javascript'"
    )


class SpiderCreate(SpiderBase):
    """创建爬虫请求模型"""

    pass


class SpiderUpdate(BaseModel):
    """更新爬虫请求模型"""

    name: Optional[str] = Field(None, description="爬虫名称")
    description: Optional[str] = Field(None, description="爬虫描述")
    module_path: Optional[str] = Field(None, description="爬虫模块路径")
    class_name: Optional[str] = Field(None, description="爬虫类名")
    is_active: Optional[bool] = Field(None, description="是否激活")
    language: Optional[str] = Field(
        None, description="爬虫语言类型，支持 'python' 和 'javascript'"
    )


class SpiderResponse(SpiderBase):
    """爬虫响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
