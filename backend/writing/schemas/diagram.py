# -*- coding: utf-8 -*-
"""结构化图表 Pydantic 模型"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class DiagramPosition(BaseModel):
    """节点坐标"""

    x: float = 0
    y: float = 0


class DiagramSize(BaseModel):
    """节点尺寸"""

    width: float = Field(160, gt=0)
    height: float = Field(56, gt=0)


class DiagramNodeStyle(BaseModel):
    """受控节点样式"""

    shape: Literal["rectangle", "rounded", "database", "decision"] = "rectangle"


class DiagramNode(BaseModel):
    """结构化图表节点"""

    id: str
    type: str = "default"
    text: str = "新节点"
    position: DiagramPosition = Field(default_factory=DiagramPosition)
    size: DiagramSize = Field(default_factory=DiagramSize)
    style: DiagramNodeStyle = Field(default_factory=DiagramNodeStyle)

    @field_validator("id", "type")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class DiagramEdge(BaseModel):
    """结构化图表连线"""

    id: str
    source: str
    target: str
    text: str = ""
    type: str = "step"

    @field_validator("id", "source", "target", "type")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class DiagramDocument(BaseModel):
    """可编辑图表文档 JSON"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str = "未命名图表"
    type: str = "generic"
    chapter_key: Optional[str] = Field(None, alias="chapterKey")
    version: int = Field(1, ge=1)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    viewport: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "title", "type")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value

    @model_validator(mode="after")
    def validate_edges(self):
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids or edge.target not in node_ids:
                raise ValueError(f"连线 {edge.id} 引用了不存在的节点")
        return self


class DiagramCreate(BaseModel):
    """创建图表请求"""

    title: str = Field(..., min_length=1, max_length=100)
    type: str = Field("generic", min_length=1, max_length=50)
    chapter_key: Optional[str] = Field(None, max_length=50)
    data: Dict[str, Any] = Field(default_factory=dict)


class DiagramUpdate(BaseModel):
    """更新图表请求"""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    chapter_key: Optional[str] = Field(None, max_length=50)
    data: Optional[Dict[str, Any]] = None


class DiagramResponse(BaseModel):
    """图表响应"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    paper_id: str
    title: str
    type: str
    chapter_key: Optional[str]
    data_json: DiagramDocument
    version: int
    created_at: datetime
    updated_at: Optional[datetime]
