# -*- coding: utf-8 -*-
"""论文主表模型"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.dependencies import Base

if TYPE_CHECKING:
    from .chapter import Chapter
    from .design import Design


class Paper(Base):
    """论文主表"""
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment="论文ID")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="论文题目")
    techs: Mapped[List[str]] = mapped_column(JSON, nullable=False, comment="技术栈列表")
    word_level: Mapped[str] = mapped_column(String(20), default="medium", comment="字数档位: small/medium/large")
    style: Mapped[str] = mapped_column(String(50), default="严谨学术", comment="写作风格")
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="用户补充需求")

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="draft", comment="状态: draft/generating/done/updating")
    mode: Mapped[str] = mapped_column(String(20), default="template", comment="生成模式: template/ai")

    # 统计
    word_count: Mapped[int] = mapped_column(Integer, default=0, comment="总字数")
    chapter_count: Mapped[int] = mapped_column(Integer, default=0, comment="章节数")
    chart_count: Mapped[int] = mapped_column(Integer, default=0, comment="图表数")

    # 时间
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="生成时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, comment="更新时间")

    # 备注
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注信息")

    # 外键
    user_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="用户ID（预留）")
    design_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("designs.id"), nullable=True, comment="系统设定ID")

    # 关联关系 - 多个 Chapter 属于一个 Paper（一对多）
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter",
        back_populates="paper",
        order_by="Chapter.seq",
        cascade="all, delete-orphan",
    )
    # Paper 属于一个 Design（多对一）
    design: Mapped[Optional["Design"]] = relationship(
        "Design",
        back_populates="papers",
        foreign_keys=[design_id],
    )

    def __repr__(self):
        return f"<Paper(id={self.id}, title={self.title[:20]}...)>"