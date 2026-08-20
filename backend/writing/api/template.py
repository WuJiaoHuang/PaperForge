# -*- coding: utf-8 -*-
"""模板配置 API 路由"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db
from ..services import TemplateService
from ..schemas import (
    TemplateConfigCreate,
    TemplateConfigUpdate,
    TemplateConfigResponse,
    ChapterOrderUpdate,
    CustomChapterCreate,
    TemplateApplyRequest,
    TemplatePreviewResponse,
)

router = APIRouter(prefix="/templates", tags=["模板配置"])
template_service = TemplateService()


@router.get("/available")
async def get_available_chapters():
    """获取所有可用章节"""
    return {
        "chapters": template_service.get_available_chapters()
    }


@router.get("", response_model=list[TemplateConfigResponse])
async def list_templates(
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取模板配置列表"""
    if user_id:
        configs = await template_service.get_user_configs(db, user_id)
    else:
        configs = await template_service.get_user_configs(db, None)
    return configs


@router.get("/default", response_model=TemplateConfigResponse)
async def get_default_template(
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取默认模板配置"""
    config = await template_service.get_default_config(db, user_id)
    if not config:
        raise HTTPException(status_code=404, detail="未找到默认模板")
    return config


@router.get("/{config_id}", response_model=TemplateConfigResponse)
async def get_template(
    config_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取模板配置详情"""
    config = await template_service.get_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模板不存在")
    return config


@router.post("", response_model=TemplateConfigResponse)
async def create_template(
    data: TemplateConfigCreate,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """创建模板配置"""
    return await template_service.create_config(db, data, user_id)


@router.put("/{config_id}", response_model=TemplateConfigResponse)
async def update_template(
    config_id: str,
    data: TemplateConfigUpdate,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """更新模板配置"""
    config = await template_service.update_config(db, config_id, data, user_id)
    if not config:
        raise HTTPException(status_code=404, detail="模板不存在")
    return config


@router.delete("/{config_id}")
async def delete_template(
    config_id: str,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """删除模板配置"""
    try:
        success = await template_service.delete_config(db, config_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="模板不存在")
        return {"message": "模板已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{config_id}/order", response_model=TemplateConfigResponse)
async def update_chapter_order(
    config_id: str,
    data: ChapterOrderUpdate,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """调整章节顺序"""
    config = await template_service.update_chapter_order(
        db, config_id, data.chapter_order, user_id
    )
    if not config:
        raise HTTPException(status_code=404, detail="模板不存在")
    return config


@router.post("/{config_id}/custom-chapter", response_model=TemplateConfigResponse)
async def add_custom_chapter(
    config_id: str,
    data: CustomChapterCreate,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """添加自定义章节"""
    config = await template_service.add_custom_chapter(db, config_id, data, user_id)
    if not config:
        raise HTTPException(status_code=404, detail="模板不存在")
    return config


@router.delete("/{config_id}/custom-chapter/{chapter_key}")
async def remove_custom_chapter(
    config_id: str,
    chapter_key: str,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """移除自定义章节"""
    config = await template_service.remove_custom_chapter(db, config_id, chapter_key, user_id)
    if not config:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"message": f"自定义章节 {chapter_key} 已移除"}


@router.post("/apply", response_model=dict)
async def apply_template_to_paper(
    data: TemplateApplyRequest,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """应用模板到论文"""
    try:
        result = await template_service.apply_template_to_paper(
            db,
            data.paper_id,
            data.template_config_id,
            data.regenerate_existing,
            user_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{config_id}/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    config_id: str,
    db: AsyncSession = Depends(get_db),
):
    """预览模板配置"""
    config = await template_service.get_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模板不存在")

    chapters = config.get_all_chapters()
    return TemplatePreviewResponse(
        config_id=config.id,
        name=config.name,
        chapters=chapters,
        custom_count=len(config.custom_chapters),
        total_count=len(chapters),
    )