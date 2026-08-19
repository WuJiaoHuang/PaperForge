# -*- coding: utf-8 -*-
"""PaperForge V2 日志工具"""

import logging
import sys
from datetime import datetime
from typing import Optional

from .sse import ProgressPublisher


class Logger:
    """统一日志管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.logger = logging.getLogger("paperforge")
        self.logger.setLevel(logging.DEBUG)
        
        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # SSE 发布器（可注入）
        self._publisher: Optional[ProgressPublisher] = None
    
    def set_publisher(self, publisher: ProgressPublisher):
        """注入 SSE 发布器"""
        self._publisher = publisher
    
    def _log(self, level: str, message: str, *args, **kwargs):
        """内部日志方法"""
        method = getattr(self.logger, level.lower(), self.logger.info)
        if args:
            message = message % args
        method(message)
        
        # 同时推送到 SSE
        if self._publisher:
            import asyncio
            try:
                # 尝试异步推送
                asyncio.create_task(self._publisher.publish_log(level, message))
            except RuntimeError:
                # 没有事件循环，跳过
                pass
    
    def debug(self, msg: str, *args, **kwargs):
        self._log("DEBUG", msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log("INFO", msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log("WARNING", msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self._log("ERROR", msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self._log("CRITICAL", msg, *args, **kwargs)


# 全局日志实例
logger = Logger()