# -*- coding: utf-8 -*-
"""结构化图表模型"""

from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.dependencies import Base

if TYPE_CHECKING:
    from .paper import Paper


class Diagram(Base):
    """可编辑结构化图表"""

    __tablename__ = "diagrams"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment="图表ID")
    paper_id: Mapped[str] = mapped_column(String(32), ForeignKey("papers.id"), nullable=False, comment="所属论文ID")
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="图表标题")
    caption: Mapped[str | None] = mapped_column(String(120), nullable=True, comment="图表题注(不含图号)")
    type: Mapped[str] = mapped_column(String(50), default="generic", comment="图表类型")
    chapter_key: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="所属章节Key")
    section_key: Mapped[str | None] = mapped_column(String(80), nullable=True, comment="所属小节Key")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="同一位置排序")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否纳入论文")
    data_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, comment="结构化 Diagram JSON")
    version: Mapped[int] = mapped_column(Integer, default=1, comment="版本号")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow, comment="更新时间")

    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="diagrams",
        foreign_keys=[paper_id],
    )

    def __repr__(self):
        return f"<Diagram(id={self.id}, title={self.title[:20]}...)>"
