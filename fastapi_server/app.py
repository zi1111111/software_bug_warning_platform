
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from server.service.maintenance_service import start_scheduler, shutdown_scheduler
from server.service.base_service import router as base_router
from server.service.data_response import router as data_router

logger = logging.getLogger(__name__)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

from server.service.user_service import router as user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时
    logger.info("应用启动中...")

    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"启动过程中发生错误: {str(e)}")

    yield
    # 应用关闭时
    logger.info("应用关闭中...")
    try:
        shutdown_scheduler()
        logger.info("定时任务调度器已关闭")
    except Exception as e:
        logger.error(f"关闭调度器时出错: {str(e)}")


app = FastAPI(
    title="开源软件漏洞预警平台",
    description="开源软件漏洞预警平台",
    version="0.1.0",
    lifespan=lifespan,
)

# 挂载所有路由
app.include_router(base_router, prefix="/api")
app.include_router(data_router, prefix="/api")
app.include_router(user_router, prefix="/api")

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "服务器内部错误"}
    )


# 健康检查端点
@app.get('/health')
async def health_check():
    return {"status": "healthy", "version": app.version}

# 根路径路由
@app.get('/')
async def root():
    return {
        "message": "欢迎使用 开源软件漏洞预警平台",
        "version": app.version
    }


if __name__ == '__main__':
   import uvicorn
   uvicorn.run(
       "app:app",
       host="localhost",
       port=8000,
       reload=False,
       log_level="info"
   )

