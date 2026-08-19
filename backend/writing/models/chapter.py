# -*- coding: utf-8 -*-
"""章节表模型"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.dependencies import Base

if TYPE_CHECKING:
    from .paper import Paper


class Chapter(Base):
    """章节表"""
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment="章节ID")
    paper_id: Mapped[str] = mapped_column(String(32), nullable=False, comment="所属论文ID")

    # 章节标识
    key: Mapped[str] = mapped_column(String(20), nullable=False, comment="章节Key: summary/ch1/ch2...")
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="显示顺序")
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="章节标题（用户可修改）")
    hint: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="写作要求提示")

    # 内容
    content_md: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Markdown内容")
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="HTML内容（渲染备用）")

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="generated", comment="状态: pending/generating/generated/updated")
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为用户自定义章节")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    # 版本控制（用于智能更新）
    version: Mapped[int] = mapped_column(Integer, default=1, comment="版本号")
    design_version: Mapped[int] = mapped_column(Integer, default=1, comment="关联的系统设定版本")

    # 时间
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="生成时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, comment="更新时间")

    # 关联
    paper: Mapped["Paper"] = relationship("Paper", back_populates="chapters")

    def __repr__(self):
        return f"<Chapter(id={self.id}, key={self.key}, seq={self.seq}, title={self.title})>"