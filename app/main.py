import logging

import uvicorn

from app.api.router import app

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Starting application server...")
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        timeout_keep_alive=30,
    )
