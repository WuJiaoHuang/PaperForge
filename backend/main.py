# -*- coding: utf-8 -*-
"""PaperForge V2 FastAPI 主入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .utils import logger

# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 注册各模块路由 ==========
from .writing.api import router as writing_router

app.include_router(writing_router, prefix="/api", tags=["写作模块"])


# ========== 健康检查 ==========
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ai_available": settings.AI_PROVIDER != "none",
    }


@app.on_event("startup")
async def startup():
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动成功")
    logger.info(f"AI 提供商: {settings.AI_PROVIDER}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("应用关闭")