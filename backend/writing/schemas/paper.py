# -*- coding: utf-8 -*-
"""论文相关的 Pydantic 模型"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from .chapter import ChapterResponse
from .design import DesignResponse


class PaperCreate(BaseModel):
    """创建论文请求"""
    title: str = Field(..., min_length=1, max_length=200, description="论文题目")
    techs: List[str] = Field(default=["SpringBoot", "Vue", "MySQL"], description="技术栈")
    word_level: str = Field(default="medium", description="字数档位: small/medium/large")
    style: str = Field(default="严谨学术", description="写作风格")
    requirements: Optional[str] = Field(None, description="用户补充需求")
    template_config_id: Optional[str] = Field(None, description="模板配置ID")

    @field_validator("word_level")
    @classmethod
    def validate_word_level(cls, v: str) -> str:
        allowed = {"small", "medium", "large"}
        if v not in allowed:
            raise ValueError(f"word_level 必须是 {allowed} 之一")
        return v


class PaperUpdate(BaseModel):
    """更新论文请求"""
    title: Optional[str] = Field(None, max_length=200)
    techs: Optional[List[str]] = None
    word_level: Optional[str] = None
    style: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None


class PaperGenerateRequest(BaseModel):
    """生成论文请求"""
    paper_id: str = Field(..., description="论文ID")
    use_ai: bool = Field(False, description="是否使用AI")
    on_design_changed: bool = Field(False, description="是否因设计变更触发重新生成")


class PaperGenerateResponse(BaseModel):
    """生成论文响应"""
    task_id: str = Field(..., description="Celery任务ID")
    paper_id: str = Field(..., description="论文ID")
    status: str = Field(..., description="任务状态")


class PaperResponse(BaseModel):
    """论文详情响应"""
    id: str
    title: str
    techs: List[str]
    word_level: str
    style: str
    requirements: Optional[str]
    status: str
    mode: str
    word_count: int
    chapter_count: int
    chart_count: int
    generated_at: datetime
    updated_at: Optional[datetime]
    note: Optional[str]
    design_id: Optional[str]
    design: Optional[DesignResponse]
    chapters: List[ChapterResponse]

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """论文列表响应"""
    items: List[PaperResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaperProgress(BaseModel):
    """论文生成进度"""
    current: int = Field(..., description="当前进度")
    total: int = Field(..., description="总步数")
    stage: str = Field(..., description="当前阶段名称")
    detail: Optional[str] = Field(None, description="详情")
    progress: float = Field(..., description="进度百分比")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaperSSEEvent(BaseModel):
    """SSE 事件"""
    type: str = Field(..., description="事件类型: stage/chapter/design/done/error/log")
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)