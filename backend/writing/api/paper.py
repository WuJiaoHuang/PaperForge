# -*- coding: utf-8 -*-
"""论文 API 路由"""

import uuid
import asyncio
import os
import time
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from backend.dependencies import get_db
from backend.utils import SSEEvent, logger
from backend.tasks import generate_paper_task
from ..services import WritingService, TemplateService
from ..schemas import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperListResponse,
    PaperGenerateRequest,
    PaperGenerateResponse,
)
from ..models import Paper, Chapter

router = APIRouter(prefix="/papers", tags=["论文管理"])
writing_service = WritingService()
template_service = TemplateService()
SSE_MAX_LIFETIME_SECONDS = int(os.getenv("PAPERFORGE_SSE_MAX_LIFETIME_SECONDS", "1800"))


@router.post("", response_model=PaperResponse)
async def create_paper(
    data: PaperCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建论文草稿"""
    paper_id = uuid.uuid4().hex[:10]

    # 获取模板配置
    template_config = None
    if data.template_config_id:
        template_config = await template_service.get_config(db, data.template_config_id)
    if not template_config:
        template_config = await template_service.get_default_config(db)

    paper = Paper(
        id=paper_id,
        title=data.title,
        techs=data.techs,
        word_level=data.word_level,
        style=data.style,
        requirements=data.requirements,
        status="draft",
        mode="template",
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)

    # 如果有模板配置，应用模板
    if template_config:
        await template_service.apply_template_to_paper(
            db, paper_id, template_config.id, regenerate_existing=False
        )

    # 重新查询论文，加载关联的 chapters 和 design
    result = await db.execute(
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.chapters),
            selectinload(Paper.design),
        )
    )
    paper = result.scalar_one_or_none()

    return PaperResponse.model_validate(paper)


@router.get("", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取论文列表"""
    query = select(Paper)
    if status:
        query = query.where(Paper.status == status)

    count_query = select(func.count()).select_from(Paper)
    if status:
        count_query = count_query.where(Paper.status == status)

    total = await db.execute(count_query)
    total = total.scalar() or 0

    # 加载关联数据，避免懒加载在异步上下文外访问
    query = (
        query
        .order_by(Paper.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .options(
            selectinload(Paper.chapters),
            selectinload(Paper.design),
        )
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return PaperListResponse(
        items=[PaperResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取论文详情"""
    # 直接查询并加载关联数据
    result = await db.execute(
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.chapters),
            selectinload(Paper.design),
        )
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    return PaperResponse.model_validate(paper)


@router.put("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: str,
    data: PaperUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新论文信息"""
    paper = await writing_service._get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(paper, key):
            setattr(paper, key, value)

    await db.commit()
    await db.refresh(paper)

    # 重新加载关联数据
    result = await db.execute(
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.chapters),
            selectinload(Paper.design),
        )
    )
    paper = result.scalar_one_or_none()
    return PaperResponse.model_validate(paper)


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除论文（软删除）"""
    paper = await writing_service._get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    # 软删除：禁用所有章节
    await db.execute(
        update(Chapter).where(Chapter.paper_id == paper_id).values(is_enabled=False)
    )
    paper.status = "deleted"
    await db.commit()

    return {"message": "论文已删除"}


@router.post("/{paper_id}/generate", response_model=PaperGenerateResponse)
async def generate_paper(
    paper_id: str,
    req: PaperGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    生成论文（异步任务）

    返回 task_id，通过 SSE 监听进度
    """
    paper = await writing_service._get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    # 提交 Celery 任务
    task = generate_paper_task.delay(
        paper_id=paper_id,
        use_ai=req.use_ai,
    )

    # 更新状态
    paper.status = "generating"
    await db.commit()

    return PaperGenerateResponse(
        task_id=task.id,
        paper_id=paper_id,
        status="pending",
    )


@router.get("/{paper_id}/stream")
async def stream_paper_progress(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    SSE 流式推送论文生成进度

    当前使用数据库轮询论文状态；Redis Pub/Sub 尚未接入。
    """
    paper = await writing_service._get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    async def event_generator():
        started_at = time.monotonic()
        last_chapter_count = 0

        while True:
            if time.monotonic() - started_at >= SSE_MAX_LIFETIME_SECONDS:
                yield SSEEvent(
                    event="timeout",
                    data={
                        "type": "timeout",
                        "paper_id": paper_id,
                        "message": "生成进度监听超时，请稍后刷新论文状态",
                    },
                ).to_sse()
                break

            # 检查论文状态
            await db.refresh(paper)

            if paper.status == "done":
                yield SSEEvent(
                    event="done",
                    data={"type": "done", "paper_id": paper_id, "message": "生成完成"}
                ).to_sse()
                break

            if paper.status == "error":
                yield SSEEvent(
                    event="error",
                    data={"type": "error", "message": paper.note or "生成失败"}
                ).to_sse()
                break

            # 获取已生成的章节
            result = await db.execute(
                select(Chapter).where(
                    Chapter.paper_id == paper_id,
                    Chapter.is_enabled == True,
                    Chapter.content_md.isnot(None),
                ).order_by(Chapter.seq)
            )
            chapters = result.scalars().all()

            # 如果有新章节，推送
            if len(chapters) > last_chapter_count:
                for ch in chapters[last_chapter_count:]:
                    yield SSEEvent(
                        event="chapter",
                        data={
                            "type": "chapter",
                            "seq": ch.seq,
                            "key": ch.key,
                            "title": ch.title,
                            "content_md": ch.content_md,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    ).to_sse()
                last_chapter_count = len(chapters)

            await asyncio.sleep(2)  # 每2秒检查一次

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
