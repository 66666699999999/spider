from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse,JSONResponse
from app.services.ScreenShotService import main
import os

routerss = APIRouter()
PATHPIC = "../public/pic/test.png"

@routerss.get("/screenshot")
async def screen_shot(url: str):
    await main(url)
    if os.path.exists(PATHPIC):
        return JSONResponse(
            content={"message": "", "status": "sucess"},
            status_code=200
        )
    return HTTPException(detail="Failed to capture screenshot", status_code=500)

@routerss.get("/pic")
async def get_pic():
    return FileResponse(path=PATHPIC,media_type="image/png")