import os

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.load_config import Config
from app.database.models import Task

config = Config()

# url = "http://127.0.0.1:8000/screenshot?url=https://x.com/some1else45"
# timeout = 100000
# re = httpx.get(url=url, timeout=timeout)
# print(re.status_code)
# print(re.json())

import asyncio

url = "http://localhost:8000/tasks"
body = {
    "url": "https://example.com",
    "cron_expression": "0 0 * * *",
    "description": "测试任务",
}
headers = {"Content-Type": "application/json"}


async def test_api():
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body, headers=headers)
        print(response.status_code)
        print(response.json())
        # 检查响应状态码
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == body["url"]
        assert data["cron_expression"] == body["cron_expression"]
        assert "id" in data
        return data


async def delete_database():
    task_id = 1
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{url}/{task_id}", headers=headers)

        print(response.status_code)
        print(response.json())
        # 检查响应状态码
        assert response.status_code == 200
        data = response.json()
        return data


if __name__ == "__main__":
    task_data = asyncio.run(delete_database())
    # asyncio.run(check_database(task_data["id"]))
