from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.load_config import Config

# 加载配置
config = Config()
config_data = config.load_file()

# 获取数据库URL
DATABASE_URL = config_data.get('database', {}).get('url', 'sqlite:///./default.db')

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL
)

# 创建会话本地类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()