# 使用官方Python镜像作为基础
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_VERSION=1.6.1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install --upgrade pip && \
    pip install "poetry==$POETRY_VERSION"

# 配置Poetry不创建虚拟环境
RUN poetry config virtualenvs.create false

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装依赖
RUN poetry install --no-interaction --no-ansi

# 如果没有poetry.lock文件，则使用requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制项目代码
COPY . .

# 创建配置文件（如果不存在）
RUN if [ ! -f app/config/config.toml ]; then \
    cp app/config/config.example.toml app/config/config.toml; \
fi

# 生成加密密钥（首次运行时）
RUN python -c "import os; from cryptography.fernet import Fernet; \
key_path = 'app/config/secret.key'; \
if not os.path.exists(key_path): \
    with open(key_path, 'wb') as f: \
        f.write(Fernet.generate_key()); \
    os.chmod(key_path, 0o600); \
print('Encryption key generated or exists')"

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload=False"]