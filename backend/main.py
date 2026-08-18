# -*- coding: utf-8 -*-
"""PaperForge V0 明日展示 Demo —— FastAPI 主入口。"""

import time
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .ai_client import ai_available, generate_paper_ai, suggest_topics_ai
from .exporter import build_docx_bytes, to_markdown
from .template_engine import generate_paper, suggest_topics

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

app = FastAPI(title="PaperForge Demo", description="论文工坊 · 明日展示 Demo")


class GenerateRequest(BaseModel):
    title: str = ""
    techs: list = ["SpringBoot", "Vue", "MySQL"]
    word_level: str = "medium"
    style: str = "严谨学术"
    use_ai: bool = False


class SuggestRequest(BaseModel):
    keywords: str = ""
    techs: list = []
    count: int = 4
    batch: int = 0
    use_ai: bool = False


class ExportRequest(BaseModel):
    payload: dict


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_available": ai_available()}


@app.post("/api/generate")
def generate(req: GenerateRequest):
    title = (req.title or "").strip()
    if not title:
        return JSONResponse({"error": "请填写论文题目"}, status_code=400)
    techs = [t for t in (req.techs or []) if str(t).strip()] or ["SpringBoot", "Vue", "MySQL"]
    payload = None
    note = None
    if req.use_ai and not ai_available():
        note = "未配置 DeepSeek API Key,已使用本地模板模式"
    elif req.use_ai:
        payload = generate_paper_ai(title, techs, req.word_level, req.style)
        if payload is None:
            note = "AI 调用失败,已自动降级为本地模板模式"
    if payload is None:
        payload = generate_paper(title, techs, req.word_level, req.style)
    payload["id"] = uuid.uuid4().hex[:10]
    payload["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    if note:
        payload["note"] = note
    return payload


@app.post("/api/topics/suggest")
def suggest_topics_api(req: SuggestRequest):
    keywords = (req.keywords or "").strip()
    techs = [t for t in (req.techs or []) if str(t).strip()] or ["SpringBoot", "Vue", "MySQL"]
    count = max(1, min(req.count or 4, 6))
    note = None
    if req.use_ai and ai_available():
        topics = suggest_topics_ai(keywords, techs, count, req.batch)
        if topics:
            return {"topics": topics, "mode": "ai"}
        note = "AI 调用失败,已使用本地模板生成"
    topics = suggest_topics(keywords, techs, count, req.batch)
    resp = {"topics": topics, "mode": "template"}
    if note:
        resp["note"] = note
    return resp


@app.post("/api/export/docx")
def export_docx(req: ExportRequest):
    buf = build_docx_bytes(req.payload)
    filename = quote("论文工坊_论文初稿.docx")
    return Response(
        buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''%s" % filename},
    )


@app.post("/api/export/md")
def export_md(req: ExportRequest):
    text = to_markdown(req.payload)
    filename = quote("论文工坊_论文初稿.md")
    return Response(
        text.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''%s" % filename},
    )


app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
