# -*- coding: utf-8 -*-
"""Writing 模块业务服务"""

from .writing_service import WritingService
from .template_service import TemplateService
from .export_service import ExportService

# 单例实例（可选）
writing_service = WritingService()
template_service = TemplateService()
export_service = ExportService()

__all__ = [
    "WritingService",
    "TemplateService",
    "ExportService",
    "writing_service",
    "template_service",
    "export_service",
]