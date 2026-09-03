# -*- coding: utf-8 -*-
"""Writing 模块 API 路由"""

from fastapi import APIRouter

from .paper import router as paper_router
from .chapter import router as chapter_router
from .diagram import router as diagram_router
from .template import router as template_router
from .export import router as export_router

# 创建模块路由
router = APIRouter(prefix="/writing", tags=["写作模块"])

# 注册子路由
router.include_router(paper_router)
router.include_router(chapter_router)
router.include_router(diagram_router)
router.include_router(template_router)
router.include_router(export_router)

__all__ = ["router"]
