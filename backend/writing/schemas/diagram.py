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


class SequenceParticipant(BaseModel):
    """时序图参与者"""

    id: str
    name: str

    @field_validator("id", "name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class SequenceMessage(BaseModel):
    """时序图消息"""

    id: str
    from_: str = Field(..., alias="from")
    to: str
    text: str
    order: int = Field(1, ge=1)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id", "from_", "to", "text")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class SequencePayload(BaseModel):
    """时序图结构化源数据"""

    participants: List[SequenceParticipant] = Field(default_factory=list)
    messages: List[SequenceMessage] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_messages(self):
        participant_ids = {item.id for item in self.participants}
        for message in self.messages:
            if message.from_ not in participant_ids or message.to not in participant_ids:
                raise ValueError(f"消息 {message.id} 引用了不存在的参与者")
        return self


class UseCaseActor(BaseModel):
    """用例图参与者"""

    id: str
    name: str

    @field_validator("id", "name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class UseCaseItem(BaseModel):
    """用例"""

    id: str
    name: str

    @field_validator("id", "name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class UseCaseRelation(BaseModel):
    """参与者与用例关系"""

    actor: str
    usecase: str

    @field_validator("actor", "usecase")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class UseCasePayload(BaseModel):
    """用例图结构化源数据"""

    actors: List[UseCaseActor] = Field(default_factory=list)
    usecases: List[UseCaseItem] = Field(default_factory=list)
    relations: List[UseCaseRelation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_relations(self):
        actor_ids = {item.id for item in self.actors}
        usecase_ids = {item.id for item in self.usecases}
        for relation in self.relations:
            if relation.actor not in actor_ids or relation.usecase not in usecase_ids:
                raise ValueError("用例关系引用了不存在的参与者或用例")
        return self


class DiagramDocument(BaseModel):
    """可编辑图表文档 JSON"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str = "未命名图表"
    caption: Optional[str] = None
    type: str = "generic"
    chapter_key: Optional[str] = Field(None, alias="chapterKey")
    section_key: Optional[str] = Field(None, alias="sectionKey")
    sort_order: int = Field(0, alias="sortOrder")
    is_enabled: bool = Field(True, alias="isEnabled")
    version: int = Field(1, ge=1)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    sequence: Optional[SequencePayload] = None
    usecase: Optional[UseCasePayload] = None
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
        if self.type == "sequence":
            if self.sequence is None:
                raise ValueError("sequence 图表缺少 sequence 数据")
            return self
        if self.type == "usecase":
            if self.usecase is None:
                raise ValueError("usecase 图表缺少 usecase 数据")
            return self
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids or edge.target not in node_ids:
                raise ValueError(f"连线 {edge.id} 引用了不存在的节点")
        return self


class DiagramCreate(BaseModel):
    """创建图表请求"""

    title: str = Field(..., min_length=1, max_length=100)
    caption: Optional[str] = Field(None, max_length=120)
    type: str = Field("generic", min_length=1, max_length=50)
    chapter_key: Optional[str] = Field(None, max_length=50)
    section_key: Optional[str] = Field(None, max_length=80)
    sort_order: int = Field(0)
    is_enabled: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)


class DiagramUpdate(BaseModel):
    """更新图表请求"""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    caption: Optional[str] = Field(None, max_length=120)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    chapter_key: Optional[str] = Field(None, max_length=50)
    section_key: Optional[str] = Field(None, max_length=80)
    sort_order: Optional[int] = None
    is_enabled: Optional[bool] = None
    data: Optional[Dict[str, Any]] = None


class DiagramGenerate(BaseModel):
    """自动生成图表请求"""

    type: Literal["architecture", "module", "flow", "er", "sequence", "usecase"]
    title: str = Field(..., min_length=1, max_length=100)
    caption: Optional[str] = Field(None, max_length=120)
    chapter_key: Optional[str] = Field(None, max_length=50)
    section_key: Optional[str] = Field(None, max_length=80)
    sort_order: int = 0
    is_enabled: bool = True


class DiagramResponse(BaseModel):
    """图表响应"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    paper_id: str
    title: str
    caption: Optional[str]
    type: str
    chapter_key: Optional[str]
    section_key: Optional[str]
    sort_order: int
    is_enabled: bool
    data_json: DiagramDocument
    version: int
    created_at: datetime
    updated_at: Optional[datetime]
