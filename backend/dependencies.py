# -*- coding: utf-8 -*-
"""PaperForge V2 依赖注入"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import Settings, settings

# ========== 异步数据库引擎 ==========
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
)

# ========== 异步会话工厂 ==========
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ========== ORM 基类 ==========
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ========== 便捷的数据库上下文管理器 ==========
@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """数据库会话上下文管理器（用于服务层）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ========== 当前用户（预留，等用户系统） ==========
async def get_current_user():
    """获取当前用户（暂不实现，返回 None）"""
    return None


# ========== 获取配置 ==========
def get_settings() -> Settings:
    """获取配置（依赖注入）"""
    return settings
