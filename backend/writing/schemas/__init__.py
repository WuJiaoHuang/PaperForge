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
    ChapterRegenerateResponse,
    ChapterBatchUpdate,
)
from .design import (
    DesignCreate,
    DesignUpdate,
    DesignResponse,
    DesignDiffRequest,
    DesignAffectedChapters,
    DesignConsistencyCheck,
)
from .diagram import (
    DiagramCreate,
    DiagramUpdate,
    DiagramGenerate,
    DiagramResponse,
    DiagramDocument,
    DiagramNode,
    DiagramEdge,
)
from .template import (
    TemplateConfigCreate,
    TemplateConfigUpdate,
    TemplateConfigResponse,
    ChapterConfigItem,
    ChapterOrderUpdate,
    CustomChapterCreate,
    TemplateApplyRequest,
    TemplatePreviewResponse,
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
    "ChapterRegenerateResponse",
    "ChapterBatchUpdate",
    # Design
    "DesignCreate",
    "DesignUpdate",
    "DesignResponse",
    "DesignDiffRequest",
    "DesignAffectedChapters",
    "DesignConsistencyCheck",
    # Diagram
    "DiagramCreate",
    "DiagramUpdate",
    "DiagramGenerate",
    "DiagramResponse",
    "DiagramDocument",
    "DiagramNode",
    "DiagramEdge",
    # Template
    "TemplateConfigCreate",
    "TemplateConfigUpdate",
    "TemplateConfigResponse",
    "ChapterConfigItem",
    "ChapterOrderUpdate",
    "CustomChapterCreate",
    "TemplateApplyRequest",
    "TemplatePreviewResponse",
]
