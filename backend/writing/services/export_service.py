# -*- coding: utf-8 -*-
"""导出服务 - Word / Markdown 导出"""

import io
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.exporter import build_docx_bytes, to_markdown
from backend.utils import logger
from ..models import Paper, Chapter, Design


class ExportService:
    """导出服务"""

    async def export_docx(
        self,
        db: AsyncSession,
        paper_id: str,
        chart_images: Optional[Dict[str, bytes]] = None,
    ) -> io.BytesIO:
        """
        导出为 Word 文档
        
        Args:
            db: 数据库会话
            paper_id: 论文ID
            chart_images: 图表图片映射 {图表ID: bytes}
        
        Returns:
            Word 文档字节流
        """
        # 1. 获取论文数据
        payload = await self._build_payload(db, paper_id, chart_images)

        # 2. 生成 Word
        try:
            buf = build_docx_bytes(payload)
            logger.info(f"Word 导出成功: {paper_id}")
            return buf
        except Exception as e:
            logger.error(f"Word 导出失败: {paper_id}, error={e}")
            raise

    async def export_markdown(
        self,
        db: AsyncSession,
        paper_id: str,
    ) -> str:
        """
        导出为 Markdown
        
        Args:
            db: 数据库会话
            paper_id: 论文ID
        
        Returns:
            Markdown 文本
        """
        # 1. 获取论文数据
        payload = await self._build_payload(db, paper_id)

        # 2. 生成 Markdown
        try:
            md_text = to_markdown(payload)
            logger.info(f"Markdown 导出成功: {paper_id}")
            return md_text
        except Exception as e:
            logger.error(f"Markdown 导出失败: {paper_id}, error={e}")
            raise

    async def _build_payload(
        self,
        db: AsyncSession,
        paper_id: str,
        chart_images: Optional[Dict[str, bytes]] = None,
    ) -> Dict[str, Any]:
        """构建导出 payload"""
        # 获取论文
        paper = await db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = paper.scalar_one_or_none()
        if not paper:
            raise ValueError(f"论文不存在: {paper_id}")

        # 获取章节
        chapters = await db.execute(
            select(Chapter).where(
                Chapter.paper_id == paper_id,
                Chapter.is_enabled == True,
            ).order_by(Chapter.seq)
        )
        chapters = chapters.scalars().all()

        # 获取设计
        design = None
        if paper.design_id:
            design = await db.execute(
                select(Design).where(Design.id == paper.design_id)
            )
            design = design.scalar_one_or_none()

        # 构建章节数据
        chapters_data = []
        for ch in chapters:
            # 如果有图表图片，嵌入到内容中
            content = ch.content_md or ""
            if chart_images and ch.key in chart_images:
                # 嵌入图片
                import base64
                img_b64 = base64.b64encode(chart_images[ch.key]).decode('utf-8')
                content += f"\n\n![{ch.title}](data:image/png;base64,{img_b64})"

            chapters_data.append({
                "seq": ch.seq,
                "key": ch.key,
                "title": ch.title,
                "hint": ch.hint or "",
                "content_md": content,
                "is_custom": ch.is_custom,
            })

        # 构建 payload
        payload = {
            "id": paper.id,
            "title": paper.title,
            "techs": paper.techs,
            "word_level": paper.word_level,
            "style": paper.style,
            "requirements": paper.requirements or "",
            "system_design": design.to_dict() if design else None,
            "chapters": chapters_data,
            "chart_suggestions": [],  # TODO: 从图表服务获取
            "stats": {
                "word_count": paper.word_count,
                "chapter_count": len(chapters_data),
            },
            "mode": paper.mode,
            "generated_at": paper.generated_at.isoformat() if paper.generated_at else "",
        }

        return payload

    async def get_export_preview(
        self,
        db: AsyncSession,
        paper_id: str,
    ) -> Dict[str, Any]:
        """
        获取导出预览信息
        
        Returns:
            预览信息（章节列表、字数统计等）
        """
        paper = await db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = paper.scalar_one_or_none()
        if not paper:
            raise ValueError(f"论文不存在: {paper_id}")

        chapters = await db.execute(
            select(Chapter).where(
                Chapter.paper_id == paper_id,
                Chapter.is_enabled == True,
            ).order_by(Chapter.seq)
        )
        chapters = chapters.scalars().all()

        return {
            "paper_id": paper_id,
            "title": paper.title,
            "total_chapters": len(chapters),
            "word_count": paper.word_count,
            "chapters": [
                {
                    "seq": ch.seq,
                    "key": ch.key,
                    "title": ch.title,
                    "has_content": bool(ch.content_md),
                    "status": ch.status,
                }
                for ch in chapters
            ],
            "export_formats": ["docx", "markdown"],
        }