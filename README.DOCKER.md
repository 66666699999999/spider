# Docker部署指南

本指南介绍如何使用Docker和Docker Compose部署Spider应用。

## 前提条件
- 安装Docker：[官方安装指南](https://docs.docker.com/get-docker/)
- 安装Docker Compose：[官方安装指南](https://docs.docker.com/compose/install/)

## 环境配置
1. 复制环境变量模板文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑`.env`文件，设置必要的环境变量：
   ```env
   # 应用配置
   DEBUG=False

   # 数据库配置
   DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/spider_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=password
   POSTGRES_DB=spider_db

   # 安全配置
   # 生成方式: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   SECRET_KEY=your-secret-key-here

   # 数据库连接池配置
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   DB_POOL_RECYCLE=3600
   DB_COMMAND_TIMEOUT=30
   DB_USE_SSL=False
   ```

3. 确保`app/config/config.toml`文件存在：
   ```bash
   cp app/config/config.example.toml app/config/config.toml
   ```

## 部署步骤

### 使用Docker Compose（推荐）
1. 构建并启动容器：
   ```bash
   docker-compose up --build -d
   ```

2. 查看容器状态：
   ```bash
   docker-compose ps
   ```

3. 查看应用日志：
   ```bash
   docker-compose logs -f web
   ```

4. 访问应用：http://localhost:8000

### 手动构建Docker镜像
1. 构建镜像：
   ```bash
   docker build -t spider-app .
   ```

2. 运行容器：
   ```bash
   docker run -d -p 8000:8000 --env-file .env spider-app
   ```

## 数据持久化
- 数据库数据存储在Docker卷`postgres_data`中，不会因容器重启而丢失
- 配置文件和代码通过挂载卷同步，方便开发和调试

## 生产环境注意事项
1. **安全性**：
   - 切勿将`.env`文件提交到版本控制系统
   - 生成强密码和密钥：`SECRET_KEY`、`POSTGRES_PASSWORD`
   - 在生产环境启用SSL：设置`DB_USE_SSL=True`

2. **性能优化**：
   - 根据实际负载调整数据库连接池配置
   - 考虑使用Docker Swarm或Kubernetes进行编排

3. **监控与日志**：
   - 配置日志收集系统
   - 定期备份数据库

## 常见问题

### 1. 数据库连接失败
- 检查`.env`文件中的数据库配置是否正确
- 确保PostgreSQL容器已启动并运行
- 查看容器日志获取详细错误信息

### 2. 加密密钥相关问题
- 生成新密钥：`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- 确保`app/config/secret.key`文件存在且权限正确

### 3. 端口冲突
- 如果8000端口已被占用，修改`docker-compose.yml`中的端口映射