# -*- coding: utf-8 -*-
"""系统设定相关的 Pydantic 模型"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DesignCreate(BaseModel):
    paper_id: Optional[str] = None
    modules: List[Dict[str, str]] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    tables: List[Dict[str, str]] = Field(default_factory=list)
    features: List[Dict[str, str]] = Field(default_factory=list)
    domain_note: Optional[str] = None


class DesignUpdate(BaseModel):
    modules: Optional[List[Dict[str, str]]] = None
    roles: Optional[List[str]] = None
    tables: Optional[List[Dict[str, str]]] = None
    features: Optional[List[Dict[str, str]]] = None
    domain_note: Optional[str] = None


class DesignResponse(BaseModel):
    id: str
    paper_id: Optional[str] = None
    modules: List[Dict[str, str]] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    tables: List[Dict[str, str]] = Field(default_factory=list)
    features: List[Dict[str, str]] = Field(default_factory=list)
    domain_note: Optional[str] = None
    version: int = 1

    class Config:
        from_attributes = True


class DesignDiffRequest(BaseModel):
    old_design: Dict[str, Any] = Field(default_factory=dict)
    new_design: Dict[str, Any] = Field(default_factory=dict)


class DesignAffectedChapters(BaseModel):
    affected: List[str] = Field(default_factory=list)


class DesignConsistencyCheck(BaseModel):
    consistent: bool = True
    issues: List[str] = Field(default_factory=list)
