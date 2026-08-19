# -*- coding: utf-8 -*-
"""PaperForge V2 全局配置管理"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类 - 从环境变量读取"""
    
    # ========== 应用基础 ==========
    APP_NAME: str = "PaperForge"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # ========== 数据库 ==========
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "paperforge"
    
    @property
    def DATABASE_URL(self) -> str:
        """同步数据库连接URL（SQLAlchemy）"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        """异步数据库连接URL（SQLAlchemy async）"""
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    # ========== Redis ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ========== Celery ==========
    CELERY_BROKER_URL: Optional[str] = None  # 默认使用 REDIS_URL
    CELERY_RESULT_BACKEND: Optional[str] = None  # 默认使用 REDIS_URL
    
    @property
    def CELERY_BROKER(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL
    
    @property
    def CELERY_BACKEND(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL
    
    # ========== AI 服务（智谱 GLM + DeepSeek 兼容） ==========
    # 智谱 GLM-4
    ZHIPU_API_KEY: Optional[str] = None
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPU_MODEL: str = "glm-4-flash"  # glm-4-plus / glm-4-flash
    
    # DeepSeek（兼容 OpenAI 接口）
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # Embedding 模型
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # 或智谱 embedding-2
    
    @property
    def AI_PROVIDER(self) -> str:
        """当前可用的AI提供商: zhipu / deepseek / none"""
        if self.ZHIPU_API_KEY:
            return "zhipu"
        if self.DEEPSEEK_API_KEY:
            return "deepseek"
        return "none"
    
    # ========== 阿里云 OSS ==========
    OSS_ACCESS_KEY: Optional[str] = None
    OSS_SECRET_KEY: Optional[str] = None
    OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    OSS_BUCKET: str = "paperforge"
    OSS_PREFIX: str = "uploads/"
    
    # ========== CORS ==========
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # ========== 分页 ==========
    PAGE_SIZE: int = 20
    
    # ========== 论文生成 ==========
    MAX_WORD_COUNT: int = 20000  # 最大字数限制
    DEFAULT_WORD_LEVEL: str = "medium"  # small / medium / large
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 单例实例
settings = Settings()