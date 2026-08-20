# -*- coding: utf-8 -*-
"""Writing 模块数据模型"""

from .paper import Paper
from .chapter import Chapter
from .design import Design
from .template_config import TemplateConfig

__all__ = [
    "Paper",
    "Chapter",
    "Design",
    "TemplateConfig",
]