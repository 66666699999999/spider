from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from app.services.screen_shot_service import main
import os
from app.config.load_config import Config

router = APIRouter()
config = Config()

@router.get("/screenshot")
async def screen_shot(url: str) -> JSONResponse:
    await main(url)
    config_data = config.load_file()
    screenshot_path = config.ROOT_PATH / config_data["paths"]["screenshot"]
    if os.path.exists(screenshot_path):
        return JSONResponse(
            content={"message": "Screenshot captured successfully", "status": "success"},
            status_code=200
        )
    return HTTPException(detail="Failed to capture screenshot", status_code=500)

@router.get("/pic")
async def get_pic() -> FileResponse:
    config_data = config.load_file()
    screenshot_path = config.ROOT_PATH / config_data["paths"]["screenshot"]
    if os.path.exists(screenshot_path):
        return FileResponse(path=screenshot_path, media_type="image/png")
    raise HTTPException(detail="Screenshot not found", status_code=404)