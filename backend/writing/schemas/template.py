# -*- coding: utf-8 -*-
"""模板配置相关的 Pydantic 模型"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class ChapterConfigItem(BaseModel):
    key: str
    default_title: str
    hint: str = ""
    group: str = "正文"


class TemplateConfigCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    chapter_order: List[Dict[str, Any]] = Field(default_factory=list)
    chapter_configs: List[ChapterConfigItem] = Field(default_factory=list)
    is_default: bool = False
    user_id: Optional[str] = None


class TemplateConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    chapter_order: Optional[List[Dict[str, Any]]] = None
    chapter_configs: Optional[List[ChapterConfigItem]] = None
    is_default: Optional[bool] = None


class TemplateConfigResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    chapter_order: List[Dict[str, Any]] = Field(default_factory=list)
    chapter_configs: List[ChapterConfigItem] = Field(default_factory=list)
    is_default: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChapterOrderUpdate(BaseModel):
    order: List[str] = Field(default_factory=list)


class CustomChapterCreate(BaseModel):
    title: str = Field(..., max_length=100)
    hint: Optional[str] = None
    seq: int = 99


class TemplateApplyRequest(BaseModel):
    template_id: str


class TemplatePreviewResponse(BaseModel):
    template_id: str
    chapters: List[Dict[str, Any]] = Field(default_factory=list)
