from app.database.database import engine, Base
from app.database.models import Task

# 创建所有表
Base.metadata.create_all(bind=engine)

print("数据库表创建完成！")