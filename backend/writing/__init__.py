# -*- coding: utf-8 -*-
"""Writing 模块 - 成员1：论文写作与导出"""

from .api import router
from .services import (
    WritingService,
    TemplateService,
    ExportService,
    writing_service,
    template_service,
    export_service,
)
from .models import Paper, Chapter, Design, TemplateConfig

__all__ = [
    "router",
    "WritingService",
    "TemplateService",
    "ExportService",
    "writing_service",
    "template_service",
    "export_service",
    "Paper",
    "Chapter",
    "Design",
    "TemplateConfig",
]