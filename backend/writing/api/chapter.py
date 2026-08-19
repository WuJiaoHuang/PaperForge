# -*- coding: utf-8 -*-
"""章节 API 路由"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db
from backend.tasks import regenerate_chapter_task
from ..services import WritingService
from ..schemas import (
    ChapterResponse,
    ChapterUpdate,
    ChapterRegenerateRequest,
    ChapterRegenerateResponse,
)

router = APIRouter(prefix="/papers/{paper_id}/chapters", tags=["章节管理"])
writing_service = WritingService()


@router.get("", response_model=list[ChapterResponse])
async def list_chapters(
    paper_id: str,
    enabled_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """获取论文的所有章节"""
    paper = await writing_service._get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    from sqlalchemy import select
    from ..models import Chapter

    query = select(Chapter).where(Chapter.paper_id == paper_id)
    if enabled_only:
        query = query.where(Chapter.is_enabled == True)
    query = query.order_by(Chapter.seq)

    result = await db.execute(query)
    chapters = result.scalars().all()
    return chapters


@router.get("/{chapter_key}", response_model=ChapterResponse)
async def get_chapter(
    paper_id: str,
    chapter_key: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个章节"""
    chapter = await writing_service._get_chapter(db, paper_id, chapter_key)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return chapter


@router.put("/{chapter_key}", response_model=ChapterResponse)
async def update_chapter(
    paper_id: str,
    chapter_key: str,
    data: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新章节（标题、内容、顺序等）"""
    chapter = await writing_service._get_chapter(db, paper_id, chapter_key)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(chapter, key):
            setattr(chapter, key, value)

    await db.commit()
    await db.refresh(chapter)
    return chapter


@router.post("/{chapter_key}/regenerate", response_model=ChapterRegenerateResponse)
async def regenerate_chapter(
    paper_id: str,
    chapter_key: str,
    req: ChapterRegenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    重新生成章节（异步任务）
    
    支持用户修改意见，AI 会根据意见调整内容
    """
    chapter = await writing_service._get_chapter(db, paper_id, chapter_key)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    # 提交 Celery 任务
    task = regenerate_chapter_task.delay(
        paper_id=paper_id,
        chapter_key=chapter_key,
        instructions=req.instructions,
        use_ai=req.use_ai,
    )

    # 更新状态
    chapter.status = "generating"
    await db.commit()

    return ChapterRegenerateResponse(
        task_id=task.id,
        chapter_key=chapter_key,
        status="pending",
    )


@router.delete("/{chapter_key}")
async def delete_chapter(
    paper_id: str,
    chapter_key: str,
    db: AsyncSession = Depends(get_db),
):
    """删除章节（软删除）"""
    chapter = await writing_service._get_chapter(db, paper_id, chapter_key)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    if chapter.is_custom:
        chapter.is_enabled = False
        await db.commit()
        return {"message": "章节已删除"}

    raise HTTPException(status_code=400, detail="不能删除系统内置章节")


@router.post("/reorder")
async def reorder_chapters(
    paper_id: str,
    chapter_order: list[str],
    db: AsyncSession = Depends(get_db),
):
    """批量调整章节顺序"""
    paper = await writing_service._get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    from sqlalchemy import select, update
    from ..models import Chapter

    for seq, key in enumerate(chapter_order):
        await db.execute(
            update(Chapter)
            .where(Chapter.paper_id == paper_id, Chapter.key == key)
            .values(seq=seq)
        )

    await db.commit()
    return {"message": "章节顺序已更新"}