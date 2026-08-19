# -*- coding: utf-8 -*-
"""导出 API 路由"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db
from ..services import ExportService

router = APIRouter(prefix="/export", tags=["导出"])
export_service = ExportService()


@router.get("/{paper_id}/preview")
async def export_preview(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取导出预览信息"""
    return await export_service.get_export_preview(db, paper_id)


@router.post("/{paper_id}/docx")
async def export_docx(
    paper_id: str,
    include_charts: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """
    导出 Word 文档
    
    返回 .docx 文件下载
    """
    try:
        # TODO: 获取图表图片（从图表服务）
        chart_images = None
        if include_charts:
            # chart_images = await chart_service.get_chart_images(paper_id)
            pass

        buf = await export_service.export_docx(db, paper_id, chart_images)

        return Response(
            buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="论文工坊_论文初稿_{paper_id}.docx"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/{paper_id}/markdown")
async def export_markdown(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    导出 Markdown 文档
    
    返回 .md 文件下载
    """
    try:
        md_text = await export_service.export_markdown(db, paper_id)

        return Response(
            md_text.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="论文工坊_论文初稿_{paper_id}.md"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/{paper_id}/docx/stream")
async def export_docx_stream(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    流式导出 Word 文档（大文件场景）
    
    使用 StreamingResponse 分块传输
    """
    try:
        buf = await export_service.export_docx(db, paper_id)

        async def stream_generator():
            data = buf.getvalue()
            chunk_size = 8192
            for i in range(0, len(data), chunk_size):
                yield data[i:i + chunk_size]

        return StreamingResponse(
            stream_generator(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="论文工坊_论文初稿_{paper_id}.docx"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")