import httpx
import os
from app.config.load_config import Config
config = Config()

url = "http://127.0.0.1:8000/screenshot?url=https://x.com/some1else45"
timeout = 100000
re = httpx.get(url=url, timeout=timeout)
print(re.status_code)
print(re.json())