from fastapi import FastAPI
from app.api.router import routerss
import uvicorn
import os
from pathlib import Path

FILE = Path(__file__).resolve()
project_root = FILE.parents[1]

app = FastAPI(title="Auto work API")
app.include_router(routerss)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")