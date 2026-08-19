# -*- coding: utf-8 -*-
"""系统设定表模型"""

from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.dependencies import Base

if TYPE_CHECKING:
    from .paper import Paper


class Design(Base):
    """系统设定表 - 保证全篇一致性"""
    __tablename__ = "designs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment="设定ID")
    paper_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="所属论文ID")

    # 核心设定（JSON 存储）
    modules: Mapped[List[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="模块列表: [{'name': '用户管理', 'desc': '...'}]"
    )
    roles: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="角色列表: ['管理员', '普通用户']"
    )
    tables: Mapped[List[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="数据表列表: [{'name': 'sys_user', 'title': '用户信息表', 'desc': '...'}]"
    )
    features: Mapped[List[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="功能列表: [{'module': '用户管理', 'desc': '...'}]"
    )
    domain_note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="领域说明")

    # 版本控制
    version: Mapped[int] = mapped_column(Integer, default=1, comment="版本号")
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否最新版本")

    # 时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, comment="更新时间")

    # 关联
    papers: Mapped[List["Paper"]] = relationship("Paper", back_populates="design", foreign_keys=[Design.paper_id])

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "modules": self.modules,
            "roles": self.roles,
            "tables": self.tables,
            "features": self.features,
            "domain_note": self.domain_note,
            "version": self.version,
        }

    def __repr__(self):
        return f"<Design(id={self.id}, version={self.version}, is_latest={self.is_latest})>"