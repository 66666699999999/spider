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
    wget \
    gnupg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 安装Puppeteer依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*


# 安装Poetry
RUN pip install --upgrade pip && \
    pip install "poetry==$POETRY_VERSION"

# 配置Poetry不创建虚拟环境
RUN poetry config virtualenvs.create false

# 复制依赖文件
COPY requirements.txt .
COPY package.json package-lock.json* ./

# 安装Python依赖
RUN pip install -r requirements.txt

# 处理npm依赖 - 预防ENOTEMPTY错误
RUN if [ -f "package.json" ]; then \
        rm -rf node_modules package-lock.json 2>/dev/null || true; \
        npm cache clean --force; \
        npm ci --prefer-offline --no-audit --no-fund --quiet || \
        (npm install --prefer-offline --no-audit --no-fund --quiet; exit 0); \
    fi

# 复制项目代码
COPY . .

# 创建配置文件（如果不存在）
#RUN if [ ! -f app/config/config.toml ]; then \
#        cp app/config/config.example.toml app/config/config.toml; \
#    fi

# 设置权限避免npm问题
#RUN find . -type d -name "node_modules" -exec chmod -R 755 {} \; 2>/dev/null || true

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
