import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
DATABASE_URL = (f"mysql+pymysql://"
                f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')
                }@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

#配置连接池
engine = create_engine(
    DATABASE_URL,
    pool_size=20,       # 常规连接数
    max_overflow=30,    # 最大溢出连接数
    pool_timeout=60,    # 获取连接超时时间(秒)
    pool_recycle=3600, # 连接回收时间(秒)
    connect_args={
        "init_command": "SET time_zone = '+00:00'"  # 强制 UTC
    },


)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#SQLAlchemy ORM模型基类 无需编写sql
Base = declarative_base()

#DB链接
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()