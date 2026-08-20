# -*- coding: utf-8 -*-
"""PaperForge V2 Celery 任务模块"""

from .celery_app import celery_app
from .paper_tasks import (
    generate_paper_task,
    regenerate_chapter_task,
    export_paper_task,
)

__all__ = [
    "celery_app",
    "generate_paper_task",
    "regenerate_chapter_task",
    "export_paper_task",
]