# -*- coding: utf-8 -*-
"""结构化图表 API 路由"""

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dependencies import get_db
from ..models import Diagram, Paper
from ..schemas import DiagramCreate, DiagramDocument, DiagramGenerate, DiagramResponse, DiagramUpdate
from ..services.diagram_generator import generate_diagram_document

router = APIRouter(prefix="/papers/{paper_id}/diagrams", tags=["结构化图表"])


async def _get_paper(db: AsyncSession, paper_id: str) -> Optional[Paper]:
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    return result.scalar_one_or_none()


async def _get_paper_context(db: AsyncSession, paper_id: str) -> Optional[Paper]:
    result = await db.execute(
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.design),
            selectinload(Paper.design_versions),
            selectinload(Paper.chapters),
        )
    )
    return result.scalar_one_or_none()


async def _get_diagram(db: AsyncSession, paper_id: str, diagram_id: str) -> Optional[Diagram]:
    result = await db.execute(
        select(Diagram).where(Diagram.paper_id == paper_id, Diagram.id == diagram_id)
    )
    return result.scalar_one_or_none()


def _build_document(
    diagram_id: str,
    title: str,
    caption: Optional[str],
    diagram_type: str,
    chapter_key: Optional[str],
    section_key: Optional[str],
    sort_order: int,
    is_enabled: bool,
    version: int,
    data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    payload = dict(data or {})
    payload["id"] = diagram_id
    payload["title"] = title
    payload["caption"] = caption or title
    payload["type"] = diagram_type
    payload["chapterKey"] = chapter_key
    payload["sectionKey"] = section_key
    payload["sortOrder"] = sort_order
    payload["isEnabled"] = is_enabled
    payload["version"] = version
    payload.setdefault("nodes", [])
    payload.setdefault("edges", [])
    payload.setdefault("sequence", None)
    payload.setdefault("usecase", None)
    payload.setdefault("viewport", {})
    payload.setdefault("metadata", {})
    try:
        document = DiagramDocument.model_validate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return document.model_dump(by_alias=True)


def _to_response(diagram: Diagram) -> DiagramResponse:
    return DiagramResponse.model_validate(
        {
            "id": diagram.id,
            "paper_id": diagram.paper_id,
            "title": diagram.title,
            "caption": diagram.caption,
            "type": diagram.type,
            "chapter_key": diagram.chapter_key,
            "section_key": diagram.section_key,
            "sort_order": diagram.sort_order,
            "is_enabled": diagram.is_enabled,
            "data_json": DiagramDocument.model_validate(diagram.data_json),
            "version": diagram.version,
            "created_at": diagram.created_at,
            "updated_at": diagram.updated_at,
        }
    )


@router.post("", response_model=DiagramResponse)
async def create_diagram(
    paper_id: str,
    data: DiagramCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建结构化图表"""
    paper = await _get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    diagram_id = "diagram_" + uuid.uuid4().hex[:10]
    version = 1
    document = _build_document(
        diagram_id,
        data.title,
        data.caption,
        data.type,
        data.chapter_key,
        data.section_key,
        data.sort_order,
        data.is_enabled,
        version,
        data.data,
    )
    diagram = Diagram(
        id=diagram_id,
        paper_id=paper_id,
        title=data.title,
        caption=data.caption or data.title,
        type=data.type,
        chapter_key=data.chapter_key,
        section_key=data.section_key,
        sort_order=data.sort_order,
        is_enabled=data.is_enabled,
        data_json=document,
        version=version,
    )
    db.add(diagram)
    await db.commit()
    await db.refresh(diagram)
    return _to_response(diagram)


@router.post("/generate", response_model=DiagramResponse)
async def generate_diagram(
    paper_id: str,
    data: DiagramGenerate,
    db: AsyncSession = Depends(get_db),
):
    """根据当前论文持久化内容自动生成结构化图表"""
    paper = await _get_paper_context(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    diagram_id = "diagram_" + uuid.uuid4().hex[:10]
    design = paper.design
    if design is None and paper.design_versions:
        design = sorted(paper.design_versions, key=lambda item: item.version, reverse=True)[0]
    document = generate_diagram_document(
        diagram_id,
        data.title,
        data.type,
        data.chapter_key,
        paper,
        design,
        paper.chapters,
    )
    document = _build_document(
        diagram_id,
        data.title,
        data.caption,
        data.type,
        data.chapter_key,
        data.section_key,
        data.sort_order,
        data.is_enabled,
        1,
        document,
    )
    diagram = Diagram(
        id=diagram_id,
        paper_id=paper_id,
        title=data.title,
        caption=data.caption or data.title,
        type=data.type,
        chapter_key=data.chapter_key,
        section_key=data.section_key,
        sort_order=data.sort_order,
        is_enabled=data.is_enabled,
        data_json=document,
        version=1,
    )
    db.add(diagram)
    await db.commit()
    await db.refresh(diagram)
    return _to_response(diagram)


@router.get("", response_model=list[DiagramResponse])
async def list_diagrams(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取论文下的所有结构化图表"""
    paper = await _get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    result = await db.execute(
        select(Diagram)
        .where(Diagram.paper_id == paper_id)
        .order_by(Diagram.chapter_key.asc(), Diagram.sort_order.asc(), Diagram.created_at.desc())
    )
    return [_to_response(item) for item in result.scalars().all()]


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    paper_id: str,
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个结构化图表"""
    diagram = await _get_diagram(db, paper_id, diagram_id)
    if not diagram:
        raise HTTPException(status_code=404, detail="图表不存在")
    return _to_response(diagram)


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    paper_id: str,
    diagram_id: str,
    data: DiagramUpdate,
    db: AsyncSession = Depends(get_db),
):
    """保存结构化图表编辑结果"""
    diagram = await _get_diagram(db, paper_id, diagram_id)
    if not diagram:
        raise HTTPException(status_code=404, detail="图表不存在")

    next_title = data.title or diagram.title
    next_caption = data.caption if data.caption is not None else diagram.caption
    next_type = data.type or diagram.type
    next_chapter_key = data.chapter_key if data.chapter_key is not None else diagram.chapter_key
    next_section_key = data.section_key if data.section_key is not None else diagram.section_key
    next_sort_order = data.sort_order if data.sort_order is not None else diagram.sort_order
    next_is_enabled = data.is_enabled if data.is_enabled is not None else diagram.is_enabled
    next_version = diagram.version + 1
    document = _build_document(
        diagram.id,
        next_title,
        next_caption,
        next_type,
        next_chapter_key,
        next_section_key,
        next_sort_order,
        next_is_enabled,
        next_version,
        data.data if data.data is not None else diagram.data_json,
    )

    diagram.title = next_title
    diagram.caption = next_caption or next_title
    diagram.type = next_type
    diagram.chapter_key = next_chapter_key
    diagram.section_key = next_section_key
    diagram.sort_order = next_sort_order
    diagram.is_enabled = next_is_enabled
    diagram.version = next_version
    diagram.data_json = document
    await db.commit()
    await db.refresh(diagram)
    return _to_response(diagram)


@router.delete("/{diagram_id}")
async def delete_diagram(
    paper_id: str,
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除结构化图表"""
    diagram = await _get_diagram(db, paper_id, diagram_id)
    if not diagram:
        raise HTTPException(status_code=404, detail="图表不存在")

    await db.delete(diagram)
    await db.commit()
    return {"message": "图表已删除"}
