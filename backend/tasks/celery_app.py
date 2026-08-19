# -*- coding: utf-8 -*-
"""PaperForge V2 Celery 应用配置"""

from celery import Celery
from celery.schedules import crontab

from ..config import settings

# 创建 Celery 应用
celery_app = Celery(
    "paperforge",
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
    include=[
        "backend.tasks.paper_tasks",
        # 后续添加其他任务模块
    ],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3000,  # 50分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # 结果保留1天
)

# 定时任务（可选）
celery_app.conf.beat_schedule = {
    # "clean-expired-tasks": {
    #     "task": "backend.tasks.cleanup.clean_expired_tasks",
    #     "schedule": crontab(hour=3, minute=0),
    # },
}

if settings.DEBUG:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )


# 自动发现任务
def autodiscover_tasks():
    """自动发现各模块的任务"""
    celery_app.autodiscover_tasks([
        "backend.writing",
        "backend.topic",
        "backend.chart",
    ], force=True)