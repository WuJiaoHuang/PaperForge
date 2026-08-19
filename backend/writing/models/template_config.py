# -*- coding: utf-8 -*-
"""模板配置表模型 - 支持可配置化"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from backend.dependencies import Base


class TemplateConfig(Base):
    """模板配置表 - 章节顺序、标题可配置"""
    __tablename__ = "template_configs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment="配置ID")
    user_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="用户ID（空为系统默认）")

    # 名称
    name: Mapped[str] = mapped_column(String(50), default="默认模板", comment="模板名称")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为系统默认模板")

    # 章节模板配置
    # 格式: [{"key": "summary", "title": "摘要与关键词", "enabled": true, "hint": "..."}]
    chapter_order: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="章节顺序与标题配置"
    )

    # 用户自定义章节
    # 格式: [{"key": "custom_1", "title": "用户自定义章节", "hint": "..."}]
    custom_chapters: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="用户自定义章节列表"
    )

    # 可用章节池（系统预定义的所有可用章节）
    # 格式: [{"key": "summary", "default_title": "摘要与关键词", "hint": "..."}]
    available_chapters: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="系统预定义章节池"
    )

    # 元数据
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="模板描述")
    version: Mapped[int] = mapped_column(Integer, default=1, comment="配置版本")

    # 时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, comment="更新时间")

    def get_enabled_chapters(self) -> List[Dict[str, Any]]:
        """获取所有启用的章节"""
        return [c for c in self.chapter_order if c.get("enabled", True)]

    def get_all_chapters(self) -> List[Dict[str, Any]]:
        """获取所有章节（内置 + 自定义）"""
        enabled = self.get_enabled_chapters()
        custom = [{
            "key": c.get("key"),
            "title": c.get("title"),
            "enabled": True,
            "is_custom": True,
            "hint": c.get("hint", ""),
        } for c in self.custom_chapters]
        return enabled + custom

    def __repr__(self):
        return f"<TemplateConfig(id={self.id}, name={self.name}, is_default={self.is_default})>"