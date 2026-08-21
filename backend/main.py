# -*- coding: utf-8 -*-
"""PaperForge 集成版主入口:master 全部功能接口 + 组员 writing 模块(可选加载)。"""

import io
import threading
import time
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .core.ai_client import (
    ai_available,
    generate_paper_ai,
    parse_chart_spec_ai,
    plantuml_chart_ai,
    regenerate_chapter_ai,
    suggest_topics_ai,
)
from .core.chart_engine import CHART_TYPES, build_chart_prompt, generate_chart_bytes, render_plantuml
from .core.exporter import build_docx_bytes, to_markdown
from .core.template_engine import (
    build_system_design,
    generate_paper,
    regenerate_chapter_template,
    suggest_topics,
)

# ---------- V2 配置(可选加载,失败不影响主功能) ----------
try:
    from .config import settings as _settings

    APP_NAME = _settings.APP_NAME
    APP_VERSION = _settings.APP_VERSION
    CORS_ORIGINS = _settings.CORS_ORIGINS
except Exception:
    APP_NAME = "PaperForge"
    APP_VERSION = "1.0.0"
    CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
FRONTEND_DIST = FRONTEND / "dist"
STATIC_DIR = FRONTEND_DIST if FRONTEND_DIST.exists() else FRONTEND

app = FastAPI(title=APP_NAME, description="论文工坊 · 毕业设计论文写作辅助系统", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 组员 writing 模块(依赖 SQLAlchemy/Celery 等,缺依赖时自动降级) ----------
writing_enabled = False
try:
    from .writing.api import router as writing_router

    app.include_router(writing_router, prefix="/api", tags=["写作模块"])
    writing_enabled = True
except Exception as exc:
    print("=" * 60)
    print("[PaperForge] writing 模块加载失败")
    print(f"[PaperForge] {type(exc).__name__}: {exc}")
    print("=" * 60)
    raise

# 内存中的生成任务(本地演示用,不持久化)
JOBS = {}
JOBS_LOCK = threading.Lock()


class GenerateRequest(BaseModel):
    title: str = ""
    techs: list = ["SpringBoot", "Vue", "MySQL"]
    word_level: str = "medium"
    style: str = "严谨学术"
    use_ai: bool = False
    requirements: str = ""


class SuggestRequest(BaseModel):
    keywords: str = ""
    techs: list = []
    count: int = 4
    batch: int = 0
    use_ai: bool = False


class ChapterRequest(BaseModel):
    title: str = ""
    techs: list = []
    word_level: str = "medium"
    style: str = "严谨学术"
    use_ai: bool = False
    chapter_key: str = ""
    chapter_title: str = ""
    hint: str = ""
    instructions: str = ""
    requirements: str = ""
    system_design: Optional[dict] = None


class ExportRequest(BaseModel):
    payload: dict


class ChartRequest(BaseModel):
    chart_type: str = ""
    title: str = ""
    material: str = ""
    techs: list = []
    use_ai: bool = False
    system_design: Optional[dict] = None


def run_generation(req: GenerateRequest, on_stage=None, on_design=None, on_chapter=None):
    title = (req.title or "").strip()
    if not title:
        raise ValueError("请填写论文题目")
    techs = [t for t in (req.techs or []) if str(t).strip()] or ["SpringBoot", "Vue", "MySQL"]
    requirements = (req.requirements or "").strip()
    payload = None
    note = None
    if req.use_ai and not ai_available():
        note = "未配置智能写作服务,已使用本地模板模式" + ("，补充需求未应用" if requirements else "")
    elif req.use_ai:
        payload = generate_paper_ai(
            title,
            techs,
            req.word_level,
            req.style,
            requirements=requirements,
            on_stage=on_stage,
            on_chapter=on_chapter,
            on_design=on_design,
        )
        if payload is None:
            note = "智能写作服务调用失败,已自动切换为本地模板模式" + ("，补充需求未应用" if requirements else "")
    if payload is None:
        payload = generate_paper(title, techs, req.word_level, req.style)
        if requirements and not req.use_ai:
            note = "本地模板模式无法应用补充需求,配置智能写作后生效"
    payload["requirements"] = requirements
    for s in payload.get("chart_suggestions") or []:
        if isinstance(s, dict):
            s["prompt"] = build_chart_prompt(s.get("type"), payload.get("system_design"), techs, title)
    payload["id"] = uuid.uuid4().hex[:10]
    payload["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    if note:
        payload["note"] = note
    return payload


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_available": ai_available(), "writing_module": writing_enabled}


@app.get("/health")
def health_v2():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "ai_available": ai_available(),
        "writing_module": writing_enabled,
    }


@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        return run_generation(req)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@app.post("/api/generate/start")
def generate_start(req: GenerateRequest):
    title = (req.title or "").strip()
    if not title:
        return JSONResponse({"error": "请填写论文题目"}, status_code=400)
    job_id = uuid.uuid4().hex[:10]
    state = {
        "status": "running",
        "stage": "准备中",
        "current": 0,
        "total": 11,
        "design": None,
        "chapters": {},
        "payload": None,
        "error": None,
    }
    with JOBS_LOCK:
        JOBS[job_id] = state
        if len(JOBS) > 50:
            for old in list(JOBS)[: len(JOBS) - 50]:
                JOBS.pop(old, None)

    def runner():
        try:
            def on_stage(current, total, stage):
                with JOBS_LOCK:
                    state["current"] = current
                    state["total"] = total
                    state["stage"] = stage

            def on_design(design):
                with JOBS_LOCK:
                    state["design"] = design

            def on_chapter(seq, key, title, hint, content_md):
                with JOBS_LOCK:
                    state["chapters"][seq] = {
                        "seq": seq,
                        "key": key,
                        "title": title,
                        "hint": hint,
                        "content_md": content_md,
                    }

            payload = run_generation(req, on_stage=on_stage, on_design=on_design, on_chapter=on_chapter)
            with JOBS_LOCK:
                state["status"] = "done"
                state["stage"] = "生成完成"
                state["current"] = state["total"]
                state["payload"] = payload
        except Exception as exc:  # pragma: no cover
            with JOBS_LOCK:
                state["status"] = "error"
                state["error"] = str(exc)

    threading.Thread(target=runner, daemon=True).start()
    return {"job_id": job_id, "total_stages": 11}


@app.get("/api/generate/status/{job_id}")
def generate_status(job_id: str):
    with JOBS_LOCK:
        state = JOBS.get(job_id)
        if not state:
            return JSONResponse({"error": "任务不存在"}, status_code=404)
        return {
            "status": state["status"],
            "stage": state["stage"],
            "current": state["current"],
            "total": state["total"],
            "error": state["error"],
        }


@app.get("/api/generate/partial/{job_id}")
def generate_partial(job_id: str):
    """返回已生成的系统设定与已完成章节,前端可边生成边展示。"""
    with JOBS_LOCK:
        state = JOBS.get(job_id)
        if not state:
            return JSONResponse({"error": "任务不存在"}, status_code=404)
        return {
            "status": state["status"],
            "stage": state["stage"],
            "current": state["current"],
            "total": state["total"],
            "design": state["design"],
            "chapters": sorted(state["chapters"].values(), key=lambda c: c["seq"]),
            "error": state["error"],
        }


@app.get("/api/generate/result/{job_id}")
def generate_result(job_id: str):
    with JOBS_LOCK:
        state = JOBS.get(job_id)
        if not state:
            return JSONResponse({"error": "任务不存在"}, status_code=404)
        if state["status"] != "done":
            return JSONResponse({"error": "任务尚未完成"}, status_code=409)
        return state["payload"]


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
        note = "智能写作服务调用失败,已使用本地模板生成"
    topics = suggest_topics(keywords, techs, count, req.batch)
    resp = {"topics": topics, "mode": "template"}
    if note:
        resp["note"] = note
    return resp


@app.post("/api/generate/chapter")
def generate_chapter_api(req: ChapterRequest):
    title = (req.title or "").strip()
    if not title:
        return JSONResponse({"error": "请填写论文题目"}, status_code=400)
    if not req.chapter_key:
        return JSONResponse({"error": "缺少章节标识"}, status_code=400)
    techs = [t for t in (req.techs or []) if str(t).strip()] or ["SpringBoot", "Vue", "MySQL"]
    design = req.system_design
    if not isinstance(design, dict):
        design = build_system_design(title, techs, req.word_level)
    note = None
    if req.use_ai and ai_available():
        content = regenerate_chapter_ai(
            title,
            techs,
            req.word_level,
            req.style,
            design,
            req.chapter_key,
            req.chapter_title or req.chapter_key,
            req.hint or "",
            req.instructions or "",
            req.requirements or "",
        )
        if content:
            return {"content_md": content, "mode": "ai"}
        has_extra = bool((req.instructions or "").strip() or (req.requirements or "").strip())
        note = (
            "智能写作服务调用失败,已使用本地模板生成,修改意见与补充需求未能应用"
            if has_extra
            else "智能写作服务调用失败,已使用本地模板生成"
        )
    content = regenerate_chapter_template(req.chapter_key, title, techs, design, req.word_level, req.style)
    if content is None:
        return JSONResponse({"error": "不支持的章节: %s" % req.chapter_key}, status_code=400)
    resp = {"content_md": content, "mode": "template"}
    if note:
        resp["note"] = note
    elif (req.requirements or "").strip() and not req.use_ai:
        resp["note"] = "本地模板模式无法应用补充需求,配置智能写作后生效"
    return resp


@app.get("/api/charts/types")
def chart_types():
    return {"types": [{"type": k, "label": v["label"], "hint": v["hint"]} for k, v in CHART_TYPES.items()]}


@app.post("/api/charts/generate")
def generate_chart(req: ChartRequest):
    techs = [t for t in (req.techs or []) if str(t).strip()]
    buf = None
    if req.use_ai and ai_available():
        src = plantuml_chart_ai(req.chart_type, req.material, req.system_design, req.title, techs)
        if src:
            png = render_plantuml(src)
            if png:
                buf = io.BytesIO(png)
    if buf is None:
        spec = None
        if req.use_ai and ai_available():
            spec = parse_chart_spec_ai(req.chart_type, req.material, req.system_design, req.title, techs)
        buf = generate_chart_bytes(req.chart_type, req.title, req.material, req.system_design, techs, spec)
    if buf is None:
        return JSONResponse({"error": "不支持的图表类型: %s" % req.chart_type}, status_code=400)
    return Response(buf.getvalue(), media_type="image/png")


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


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
