from typing import Any, Dict, List

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.load_config import Config
from app.database.database_ssh import get_db
from app.schemas.spider import SpiderCreate, SpiderResponse, SpiderUpdate
from app.services.spider_logic_service import SpiderLogicService

# 确保中文正常显示
logging.basicConfig(level=logging.INFO, encoding='utf-8')

# 添加运行爬虫的专用请求模型
class RunSpiderRequest(BaseModel):
    spider_id: int
    language: Optional[str] = 'python'
    params: Optional[dict] = None

logger = logging.getLogger(__name__)

# 创建爬虫路由器
router = APIRouter(prefix="/spiders", tags=["spiders"])


@router.post("/upload")
async def upload_spider(
    name: str = Body(...),
    description: Optional[str] = Body(None),
    language: str = Body(..., regex=r'^(python|javascript)$'),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
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
        # 验证文件类型
        if language == 'python' and not file.filename.endswith('.py'):
            raise HTTPException(
                status_code=400,
                detail="Python爬虫必须上传.py文件"
            )
        elif language == 'javascript' and not file.filename.endswith('.js'):
            raise HTTPException(
                status_code=400,
                detail="JavaScript爬虫必须上传.js文件"
            )

        # 读取文件内容
        content = await file.read()

        # 获取配置
        config = Config()
        spider_dir = config.ROOT_PATH / "app" / "spider"
        spider_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_name = file.filename
        file_path = spider_dir / file_name

        # 检查文件是否已存在
        if file_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"文件 {file_name} 已存在"
            )

        # 写入文件
        with open(file_path, 'wb') as f:
            f.write(content)

        # 确定模块路径和类名
        if language == 'python':
            # 对于Python文件，模块路径是相对于app的路径
            module_path = f"app.spider.{file_name[:-3]}"
            # 假设类名是文件名的驼峰形式
            class_name = ''.join(word.capitalize() for word in file_name[:-3].split('_'))
        else:
            # 对于JavaScript文件，模块路径是文件的绝对路径
            module_path = str(file_path)
            # 入口函数名默认为run
            class_name = 'run'

        # 创建爬虫记录
        spider_data = SpiderCreate(
            name=name,
            description=description,
            module_path=module_path,
            class_name=class_name,
            is_active=True,
            language=language
        )

        db_spider = await SpiderLogicService.create_spider(spider_data, db)

        logger.info(f"爬虫 {name} 上传成功，文件保存至 {file_path}")

        return {
            "status": "success",
            "message": "爬虫上传成功",
            "spider": SpiderResponse.model_validate(db_spider)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"爬虫上传失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"爬虫上传失败: {str(e)}"
        )


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
    """删除爬虫，同时删除对应的脚本文件"""
    try:
        # 先获取爬虫信息
        spider = await SpiderLogicService.get_spider_by_id(spider_id, db)
        if not spider:
            raise ValueError(f"Spider with id {spider_id} not found")

        # 删除文件系统中的脚本文件
        config = Config()
        if spider.language == 'python':
            # Python文件路径: app/spider/filename.py
            file_path = config.ROOT_PATH / "app" / "spider" / f"{spider.module_path.split('.')[-1]}.py"
        else:
            # JavaScript文件路径是绝对路径
            file_path = spider.module_path

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted spider script file: {file_path}")
        else:
            logger.warning(f"Spider script file not found: {file_path}")

        # 从数据库中删除爬虫记录
        await SpiderLogicService.delete_spider(spider_id, db)

        return {"message": f"Spider {spider_id} ({spider.name}) deleted successfully"}
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=404)
    except Exception as e:
        logger.error(f"Failed to delete spider {spider_id}: {str(e)}")
        raise HTTPException(
            detail=f"Failed to delete spider: {str(e)}", status_code=500
        )
