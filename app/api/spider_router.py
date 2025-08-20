import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Body, Depends, File, HTTPException, Query,
                     UploadFile)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.spider import SpiderCreate, SpiderResponse, SpiderUpdate
from app.services.spider_logic_service import SpiderLogicService
from config.load_config import get_config_instance

# 确保中文正常显示
logging.basicConfig(level=logging.INFO, encoding="utf-8")


# 添加运行爬虫的专用请求模型
class RunSpiderRequest(BaseModel):
    spider_id: int
    language: Optional[str] = "python"
    params: Optional[dict] = None


logger = logging.getLogger(__name__)

# 创建爬虫路由器
router = APIRouter(prefix="/spiders", tags=["spiders"])


@router.post("/upload")
async def upload_spider(
    name: str = Body(...),
    description: Optional[str] = Body(None),
    language: str = Body(..., regex=r"^(python|javascript)$"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """上传爬虫脚本文件

    Args:
        name: 爬虫名称
        description: 爬虫描述
        language: 爬虫语言 (python/javascript)
        file: 爬虫脚本文件
        db: 数据库会话

    Returns:
        创建的爬虫信息
    """
    try:
        # 读取文件内容
        content = await file.read()

        # 调用service层方法处理上传逻辑
        result = await SpiderLogicService.upload_spider_file(
            name=name,
            description=description,
            language=language,
            file_content=content,
            file_name=file.filename,
            db=db,
        )

        # 转换spider对象为响应模型
        result["spider"] = SpiderResponse.model_validate(result["spider"])

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"爬虫上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬虫上传失败: {str(e)}")


@router.get("/")
async def list_spiders(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> Dict[str, Any]:
    """获取所有爬虫列表

    Args:
        db: 数据库会话
        skip: 跳过的条目数
        limit: 返回的最大条目数

    Returns:
        爬虫列表及总数
    """
    try:
        result = await SpiderLogicService.get_spiders_with_count(
            db, skip=skip, limit=limit
        )
        result["spiders"] = [
            SpiderResponse.model_validate(spider) for spider in result["spiders"]
        ]
        return result
    except Exception as e:
        logger.error(f"获取爬虫列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取爬虫列表失败: {str(e)}")


@router.post("/")
async def create_spider(
    spider_data: SpiderCreate = Body(...), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """创建新爬虫

    Args:
        spider_data: 爬虫创建数据
        db: 数据库会话

    Returns:
        创建的爬虫信息
    """
    try:
        # 调用service层方法创建爬虫
        result = await SpiderLogicService.create_spider_with_validation(spider_data, db)
        result["spider"] = SpiderResponse.model_validate(result["spider"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"爬虫创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬虫创建失败: {str(e)}")


@router.post("/run")
async def run_spider(
    request: RunSpiderRequest = Body(...), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """运行指定ID的爬虫，支持指定语言类型"""
    try:
        # 调用service层方法运行爬虫
        result = await SpiderLogicService.run_spider_with_language(
            request.spider_id, request.language, db
        )
        return result
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=400)
    except Exception as e:
        logger.error(f"运行爬虫失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"运行爬虫失败: {str(e)}")


@router.get("/{spider_id}")
async def get_spider(
    spider_id: int, db: AsyncSession = Depends(get_db)
) -> SpiderResponse:
    """获取指定ID的爬虫"""
    try:
        spider = await SpiderLogicService.get_spider_by_id(spider_id, db)
        return SpiderResponse.model_validate(spider)
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=404)
    except Exception as e:
        logger.error(f"获取爬虫详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取爬虫详情失败: {str(e)}")


@router.put("/{spider_id}")
async def update_spider(
    spider_id: int,
    spider_data: SpiderUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """更新爬虫信息"""
    try:
        updated_spider = await SpiderLogicService.update_spider(
            spider_id, spider_data, db
        )
        logger.info(f"更新爬虫 {spider_id} 成功")
        return {
            "status": "success",
            "message": "爬虫更新成功",
            "spider": SpiderResponse.model_validate(updated_spider),
        }
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=404)
    except Exception as e:
        logger.error(f"更新爬虫失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新爬虫失败: {str(e)}")


@router.delete("/{spider_id}")
async def delete_spider(
    spider_id: int, db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """删除爬虫，同时删除对应的脚本文件"""
    try:
        # 获取爬虫信息（用于返回消息）
        spider = await SpiderLogicService.get_spider_by_id(spider_id, db)

        # 调用service层方法删除爬虫
        await SpiderLogicService.delete_spider(spider_id, db)

        return {"message": f"Spider {spider_id} ({spider.name}) deleted successfully"}
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=404)
    except Exception as e:
        logger.error(f"Failed to delete spider {spider_id}: {str(e)}")
        raise HTTPException(
            detail=f"Failed to delete spider: {str(e)}", status_code=500
        )
