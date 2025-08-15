from typing import Any, Dict, List

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database_ssh import get_db
from app.schemas.spider import SpiderCreate, SpiderResponse, SpiderUpdate
from app.services.spider_logic_service import SpiderLogicService

# 添加运行爬虫的专用请求模型
class RunSpiderRequest(BaseModel):
    spider_id: int
    language: Optional[str] = 'python'
    params: Optional[dict] = None

logger = logging.getLogger(__name__)

# 创建爬虫路由器
router = APIRouter(prefix="/spiders", tags=["spiders"])


@router.get("/")
async def list_spiders(db: AsyncSession = Depends(get_db)) -> List[SpiderResponse]:
    """获取所有爬虫列表"""
    try:
        spiders = await SpiderLogicService.get_all_spiders(db)
        return [SpiderResponse.model_validate(spider) for spider in spiders]
    except Exception as e:
        raise HTTPException(
            detail=f"Failed to fetch spiders: {str(e)}", status_code=500
        )


@router.post("/")
async def create_spider(
    spider: SpiderCreate = Body(...), db: AsyncSession = Depends(get_db)
) -> SpiderResponse:
    """创建新爬虫"""
    try:
        db_spider = await SpiderLogicService.create_spider(spider, db)
        return SpiderResponse.model_validate(db_spider)
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=400)
    except Exception as e:
        raise HTTPException(
            detail=f"Failed to create spider: {str(e)}", status_code=500
        )


@router.post("/run")
async def run_spider(
    request: RunSpiderRequest = Body(...), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """运行指定ID的爬虫，支持指定语言类型"""
    try:
        # 获取爬虫信息
        spider = await SpiderLogicService.get_spider_by_id(request.spider_id, db)
        
        # 如果指定了语言且与爬虫当前语言不同，更新爬虫语言
        if request.language and spider.language != request.language:
            update_data = SpiderUpdate(language=request.language)
            spider = await SpiderLogicService.update_spider(
                request.spider_id, update_data, db
            )
            logger.info(f"Updated spider {request.spider_id} language to {request.language}")
        
        # 运行爬虫
        result = await SpiderLogicService.run_spider(request.spider_id, db)
        return result
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=400)
    except Exception as e:
        raise HTTPException(
            detail=f"Failed to run spider: {str(e)}", status_code=500
        )


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
        raise HTTPException(detail=f"Failed to fetch spider: {str(e)}", status_code=500)


@router.put("/{spider_id}")
async def update_spider(
    spider_id: int, spider: SpiderUpdate = Body(...), db: AsyncSession = Depends(get_db)
) -> SpiderResponse:
    """更新爬虫信息"""
    try:
        db_spider = await SpiderLogicService.update_spider(spider_id, spider, db)
        return SpiderResponse.model_validate(db_spider)
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=404)
    except Exception as e:
        raise HTTPException(
            detail=f"Failed to update spider: {str(e)}", status_code=500
        )


@router.delete("/{spider_id}")
async def delete_spider(
    spider_id: int, db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """删除爬虫"""
    try:
        await SpiderLogicService.delete_spider(spider_id, db)
        return {"message": f"Spider {spider_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=404)
    except Exception as e:
        raise HTTPException(
            detail=f"Failed to delete spider: {str(e)}", status_code=500
        )
