# -*- coding: utf-8 -*-
"""Writing 模块 Pydantic 模型"""

from .paper import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperListResponse,
    PaperGenerateRequest,
    PaperGenerateResponse,
)
from .chapter import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    ChapterRegenerateRequest,
    ChapterBatchUpdate,
)
from .design import (
    DesignCreate,
    DesignUpdate,
    DesignResponse,
    DesignDiffRequest,
    DesignAffectedChapters,
)
from .template import (
    TemplateConfigCreate,
    TemplateConfigUpdate,
    TemplateConfigResponse,
    ChapterOrderUpdate,
    CustomChapterCreate,
    TemplateApplyRequest,
)

__all__ = [
    # Paper
    "PaperCreate",
    "PaperUpdate",
    "PaperResponse",
    "PaperListResponse",
    "PaperGenerateRequest",
    "PaperGenerateResponse",
    # Chapter
    "ChapterCreate",
    "ChapterUpdate",
    "ChapterResponse",
    "ChapterRegenerateRequest",
    "ChapterBatchUpdate",
    # Design
    "DesignCreate",
    "DesignUpdate",
    "DesignResponse",
    "DesignDiffRequest",
    "DesignAffectedChapters",
    # Template
    "TemplateConfigCreate",
    "TemplateConfigUpdate",
    "TemplateConfigResponse",
    "ChapterOrderUpdate",
    "CustomChapterCreate",
    "TemplateApplyRequest",
]