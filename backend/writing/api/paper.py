# -*- coding: utf-8 -*-
"""论文 API 路由"""

import uuid
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db
from backend.utils import ProgressPublisher, logger
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

router = APIRouter(prefix="/papers", tags=["论文管理"])
writing_service = WritingService()
template_service = TemplateService()


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

    from ..models import Paper
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

    return paper


@router.get("", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取论文列表"""
    from sqlalchemy import select, func

    query = select(Paper)
    if status:
        query = query.where(Paper.status == status)

    count_query = select(func.count()).select_from(Paper)
    if status:
        count_query = count_query.where(Paper.status == status)

    total = await db.execute(count_query)
    total = total.scalar() or 0

    query = query.order_by(Paper.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
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
    paper = await writing_service._get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    # 加载关联数据
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.chapters),
            selectinload(Paper.design),
        )
    )
    paper = result.scalar_one_or_none()

    return paper


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
    return paper


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
    from sqlalchemy import update
    from ..models import Chapter
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
    
    使用方式：
    const eventSource = new EventSource('/api/v1/writing/papers/{id}/stream')
    eventSource.addEventListener('stage', (e) => console.log(e.data))
    eventSource.addEventListener('chapter', (e) => console.log(e.data))
    eventSource.addEventListener('done', (e) => console.log(e.data))
    """
    paper = await writing_service._get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    # 创建事件队列
    event_queue = asyncio.Queue()
    publisher = ProgressPublisher(event_queue)

    # 推送初始状态
    await publisher.publish_stage(0, 11, "准备生成", "正在初始化...")

    async def event_generator():
        try:
            # 这里会持续推送事件，直到 publisher 关闭
            # 实际进度由 Celery 任务通过 Redis 或数据库更新
            # 这里使用轮询方式检查状态
            while True:
                # 检查论文状态
                await db.refresh(paper)
                if paper.status == "done":
                    await publisher.publish_done(paper_id, "生成完成")
                    break
                elif paper.status == "draft":
                    await publisher.publish_error("生成失败")
                    break

                # 检查是否有新章节
                from sqlalchemy import select
                from ..models import Chapter
                result = await db.execute(
                    select(Chapter).where(
                        Chapter.paper_id == paper_id,
                        Chapter.is_enabled == True,
                    ).order_by(Chapter.seq)
                )
                chapters = result.scalars().all()

                # 推送已完成的章节
                for ch in chapters:
                    if ch.content_md and ch.status == "generated":
                        await publisher.publish_chapter(ch.seq, ch.key, ch.title, ch.content_md)

                await asyncio.sleep(2)  # 每2秒检查一次

            # 从队列获取事件并推送
            async for sse_event in sse_generator(event_queue):
                yield sse_event

        except asyncio.CancelledError:
            publisher.close()
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )