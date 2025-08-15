# app/database/local_database.py

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse

from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.config.load_config import get_config, get_setting

# --- 日志配置 ---
logger = logging.getLogger(__name__)


# --- ORM 基类 ---
class Base(DeclarativeBase):
    """
    SQLAlchemy ORM 基类。
    自动将类名转换为下划线形式的表名。
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """自动生成表名：MyClass -> my_class"""
        return "".join(
            f"_{char.lower()}" if char.isupper() and i != 0 else char.lower()
            for i, char in enumerate(cls.__name__)
        )


# --- 数据库连接管理 ---
class DatabaseManager:
    def __init__(self):
        self.engine: Optional[create_async_engine] = None
        self.async_session: Optional[async_sessionmaker[AsyncSession]] = None

    async def init_database(self) -> bool:
        """初始化数据库连接"""
        logger.info("Starting local database initialization...")

        try:
            # 创建数据库引擎
            db_url = os.environ.get("DATABASE_URL")
            logger.info(f"Connecting to database: {self._obfuscate_url(db_url)}")

            self.engine = create_async_engine(
                db_url,
                echo=get_setting("DEBUG", False),  # 根据环境决定是否输出SQL
                pool_pre_ping=True,  # 连接前检查
                pool_recycle=get_setting("DB_POOL_RECYCLE", 3600),
                pool_size=get_setting("DB_POOL_SIZE", 10),
                max_overflow=get_setting("DB_MAX_OVERFLOW", 20),
                connect_args={
                    "server_settings": {"application_name": "FastAPI_Spider_App"},
                    "command_timeout": get_setting("DB_COMMAND_TIMEOUT", 30),
                    "ssl": "require" if get_setting("DB_USE_SSL", False) else None,
                },
            )
            logger.info("Database engine created successfully")

            # 创建会话工厂
            self.async_session = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
            logger.info("Async session factory configured successfully")

            # 创建表
            await self._create_tables()

            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            return False

    async def _create_tables(self) -> bool:
        """创建数据库表"""
        if not self.engine:
            logger.error("Cannot create tables: Engine not initialized")
            return False

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}", exc_info=True)
            return False

    async def close_database(self):
        """关闭数据库连接"""
        if self.engine:
            try:
                await self.engine.dispose()
                logger.info("Database engine disposed")
            except Exception as e:
                logger.error(f"Error disposing database engine: {e}")
            self.engine = None
            self.async_session = None

    def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """数据库会话依赖项"""
        if not self.async_session:
            logger.error("Database session factory is not initialized")
            raise RuntimeError("Database not initialized")

        return self._get_db_session()

    async def _get_db_session(self):
        """内部方法：获取数据库会话"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise

    def _obfuscate_url(self, url):
        """混淆URL中的敏感信息"""
        parsed = urlparse(url)
        if parsed.password:
            return url.replace(parsed.password, "***")
        return url


# --- 实例化 ---
db_manager = DatabaseManager()


# --- 依赖项 ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖项，获取数据库会话"""
    async for db in db_manager.get_db():
        yield db


# --- Lifespan管理器 ---
@asynccontextmanager
async def lifespan_manager(app):
    """管理应用生命周期"""
    logger.info("Starting application with local database...")
    success = await db_manager.init_database()
    if not success:
        logger.critical("Failed to initialize database")
        raise RuntimeError("Database initialization failed")

    yield

    logger.info("Shutting down application...")
    await db_manager.close_database()
    logger.info("Application shutdown complete")
