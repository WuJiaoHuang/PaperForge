# -*- coding: utf-8 -*-
"""章节相关的 Pydantic 模型"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChapterCreate(BaseModel):
    """创建章节请求"""
    key: str = Field(..., min_length=1, max_length=20)
    seq: int
    title: str = Field(..., min_length=1, max_length=100)
    hint: Optional[str] = None
    is_custom: bool = False


class ChapterUpdate(BaseModel):
    """更新章节请求"""
    seq: Optional[int] = None
    title: Optional[str] = Field(None, max_length=100)
    content_md: Optional[str] = None
    content_html: Optional[str] = None
    status: Optional[str] = None
    is_enabled: Optional[bool] = None


class ChapterRegenerateRequest(BaseModel):
    """重新生成章节请求"""
    paper_id: str
    chapter_key: str
    instructions: str = Field(default="", description="用户修改意见")
    use_ai: bool = Field(False, description="是否使用AI")


class ChapterRegenerateResponse(BaseModel):
    """重新生成章节响应"""
    task_id: str
    chapter_key: str
    status: str


class ChapterResponse(BaseModel):
    """章节详情响应"""
    id: str
    paper_id: str
    key: str
    seq: int
    title: str
    hint: Optional[str]
    content_md: Optional[str]
    content_html: Optional[str]
    status: str
    is_custom: bool
    is_enabled: bool
    version: int
    design_version: int
    generated_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ChapterBatchUpdate(BaseModel):
    """批量更新章节请求"""
    chapters: List[ChapterUpdate]