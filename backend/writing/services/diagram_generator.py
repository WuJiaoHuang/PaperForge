# -*- coding: utf-8 -*-
"""结构化图表语义生成器"""

import re
from typing import Any, Dict, List, Optional

from backend.core.ai_client import ai_available, chat_json

DEFAULT_SIZE = {"width": 180, "height": 64}

TECH_GROUPS = {
    "frontend": {"vue", "vue3", "react", "element plus", "小程序"},
    "backend": {"spring boot", "springboot", "django", "flask", "fastapi"},
    "database": {"mysql", "postgresql", "mongodb", "opengauss"},
    "cache": {"redis"},
    "message": {"kafka", "rabbitmq", "rocketmq"},
    "search": {"elasticsearch"},
}


def generate_diagram_document(
    diagram_id: str,
    title: str,
    diagram_type: str,
    chapter_key: Optional[str],
    paper,
    design,
    chapters,
) -> Dict[str, Any]:
    """根据持久化 Paper/Design/Chapter 生成可编辑 Diagram JSON。"""
    context = _context(paper, design, chapters)
    semantic = _generate_with_ai(diagram_type, title, context) if ai_available() else None
    if semantic is not None and not _ai_is_acceptable(diagram_type, semantic):
        semantic = None
    if semantic is None:
        semantic = _generate_with_rules(diagram_type, paper, design, chapters)

    nodes, edges = _normalize_semantic(semantic, diagram_type)
    return {
        "id": diagram_id,
        "title": title,
        "type": diagram_type,
        "chapterKey": chapter_key,
        "version": 1,
        "nodes": nodes,
        "edges": edges,
        "viewport": {"x": 0, "y": 0, "zoom": 1},
        "metadata": {"source": "auto", "generator": "ai" if semantic.get("_ai") else "rules"},
    }


def _generate_with_ai(diagram_type: str, title: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    system = "你是结构化图表生成助手,只输出合法 JSON,不输出其他内容。"
    user = (
        "请根据当前论文数据生成 %s 图的业务语义节点和连线。\n"
        "图标题:%s\n论文数据:%s\n\n"
        "只输出 JSON:{\"nodes\":[{\"id\":\"frontend\",\"text\":\"Vue3 前端\",\"shape\":\"rectangle\"}],"
        "\"edges\":[{\"source\":\"frontend\",\"target\":\"backend\",\"text\":\"HTTP\"}]}\n"
        "要求:不要输出 x/y/width/height/VueFlow/ELK 字段;节点标题简短;不要臆造不存在的实体关系。"
        % (diagram_type, title, context)
    )
    data = chat_json(system, user, retries=0, max_tokens=1200, temperature=0.2)
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), list):
        return None
    data["_ai"] = True
    return data


def _generate_with_rules(diagram_type: str, paper, design, chapters) -> Dict[str, Any]:
    if diagram_type == "architecture":
        return _architecture(paper, design)
    if diagram_type == "module":
        return _module(paper, design)
    if diagram_type == "er":
        return _er(design)
    return _flow(design, chapters)


def _ai_is_acceptable(diagram_type: str, data: Dict[str, Any]) -> bool:
    texts = [str(item.get("text") or "").strip() for item in data.get("nodes") or [] if isinstance(item, dict)]
    if diagram_type == "module":
        return any(text in {"系统", "功能模块", "系统功能"} or text.endswith("系统") for text in texts)
    if diagram_type == "flow":
        return any(text == "开始" for text in texts) and any(text == "结束" for text in texts)
    if diagram_type != "architecture":
        return True
    has_user_layer = any(text in {"用户", "用户层"} for text in texts)
    has_frontend = any(("前端" in text or "Vue" in text or "React" in text) for text in texts)
    has_backend = any(("后端" in text or "服务" in text or "Spring" in text or "FastAPI" in text) for text in texts)
    has_storage = any(("数据库" in text or "MySQL" in text or "Redis" in text) for text in texts)
    return has_user_layer and has_frontend and has_backend and has_storage


def _architecture(paper, design) -> Dict[str, Any]:
    techs = _techs(paper)
    grouped = _classify_techs(techs)
    nodes = [{"id": "user", "text": "用户", "shape": "rounded"}]
    edges = []
    last = "user"

    frontend = grouped["frontend"][:2]
    if frontend:
        nodes.append({"id": "frontend", "text": _join_role(frontend, "前端"), "shape": "rectangle"})
        edges.append({"source": last, "target": "frontend", "text": "访问"})
        last = "frontend"

    backend = grouped["backend"][:2]
    if backend:
        nodes.append({"id": "backend", "text": _join_role(backend, "服务"), "shape": "rectangle"})
        edges.append({"source": last, "target": "backend", "text": "请求"})
        last = "backend"
    elif _modules(design):
        nodes.append({"id": "backend", "text": "业务服务", "shape": "rectangle"})
        edges.append({"source": last, "target": "backend", "text": "请求"})
        last = "backend"

    for group, label, edge_label, shape in [
        ("cache", "缓存", "读写缓存", "rectangle"),
        ("message", "消息", "异步消息", "rectangle"),
        ("search", "检索", "检索", "rectangle"),
        ("database", "数据库", "持久化", "database"),
    ]:
        items = grouped[group][:2]
        if items and len(nodes) < 12:
            node_id = group
            nodes.append({"id": node_id, "text": _join_role(items, label), "shape": shape})
            edges.append({"source": "backend", "target": node_id, "text": edge_label})

    if len(nodes) == 1:
        nodes.extend([
            {"id": "frontend", "text": "前端应用", "shape": "rectangle"},
            {"id": "backend", "text": "业务服务", "shape": "rectangle"},
            {"id": "database", "text": "数据存储", "shape": "database"},
        ])
        edges.extend([
            {"source": "user", "target": "frontend", "text": "访问"},
            {"source": "frontend", "target": "backend", "text": "请求"},
            {"source": "backend", "target": "database", "text": "读写"},
        ])
    return {"nodes": nodes[:12], "edges": edges}


def _module(paper, design) -> Dict[str, Any]:
    modules = _modules(design)[:14]
    root_text = _system_name(paper)
    nodes = [{"id": "system", "text": root_text, "shape": "rounded"}]
    edges = []
    if not modules:
        modules = [{"name": name} for name in ["用户管理", "信息管理", "订单管理", "后台管理"]]
    for index, module in enumerate(modules, start=1):
        node_id = f"module_{index}"
        nodes.append({"id": node_id, "text": _short_text(module.get("name") or f"模块{index}"), "shape": "rectangle"})
        edges.append({"source": "system", "target": node_id, "text": ""})
    return {"nodes": nodes[:15], "edges": edges[:14]}


def _flow(design, chapters) -> Dict[str, Any]:
    features = _features(design)
    key_feature = features[0] if features else {}
    action = _short_text(key_feature.get("desc") or key_feature.get("module") or "用户操作")
    steps = ["开始", action, "参数校验", "业务处理", "数据处理", "结果返回", "结束"]
    if action in {"参数校验", "业务处理", "数据处理", "结果返回"}:
        steps[1] = "用户操作"
    nodes = [
        {"id": f"flow_{index}", "text": text, "shape": "rounded" if index in (0, len(steps) - 1) else "rectangle"}
        for index, text in enumerate(steps)
    ]
    edges = [
        {"source": f"flow_{index}", "target": f"flow_{index + 1}", "text": ""}
        for index in range(len(steps) - 1)
    ]
    return {"nodes": nodes[:12], "edges": edges[:11]}


def _er(design) -> Dict[str, Any]:
    tables = _tables(design)[:15]
    nodes = []
    for index, table in enumerate(tables, start=1):
        name = table.get("name") or f"table_{index}"
        title = table.get("title") or table.get("desc") or ""
        text = _short_text(title) + "\n" + name if title else name
        nodes.append({"id": _safe_id(name, f"table_{index}"), "text": text, "shape": "database", "raw": table})
    edges = _infer_table_edges(nodes)
    return {"nodes": nodes, "edges": edges}


def _normalize_semantic(data: Dict[str, Any], diagram_type: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    max_nodes = {"architecture": 12, "module": 15, "flow": 12, "er": 15}.get(diagram_type, 12)
    used = set()
    id_map = {}
    nodes = []
    for index, item in enumerate(data.get("nodes") or [], start=1):
        if not isinstance(item, dict):
            continue
        raw_id = str(item.get("id") or item.get("text") or f"node_{index}")
        node_id = _unique_id(_safe_id(raw_id, f"node_{index}"), used)
        used.add(node_id)
        id_map[raw_id] = node_id
        text = _er_text(str(item.get("text") or raw_id)) if diagram_type == "er" else _short_text(str(item.get("text") or raw_id))
        shape = item.get("shape") if item.get("shape") in {"rectangle", "rounded", "database", "decision"} else "rectangle"
        if diagram_type == "er":
            shape = "database"
        nodes.append(
            {
                "id": node_id,
                "type": "default",
                "text": text,
                "position": {"x": 0, "y": 0},
                "size": dict(DEFAULT_SIZE),
                "style": {"shape": shape},
            }
        )
        if len(nodes) >= max_nodes:
            break

    valid = {node["id"] for node in nodes}
    edges = []
    for index, item in enumerate(data.get("edges") or [], start=1):
        if not isinstance(item, dict):
            continue
        source = id_map.get(str(item.get("source")), _safe_id(str(item.get("source") or ""), ""))
        target = id_map.get(str(item.get("target")), _safe_id(str(item.get("target") or ""), ""))
        if source not in valid or target not in valid or source == target:
            continue
        edges.append(
            {
                "id": _unique_id(f"edge_{source}_{target}", {edge["id"] for edge in edges}),
                "source": source,
                "target": target,
                "text": _short_text(str(item.get("text") or ""), 8),
                "type": "step",
            }
        )
    return nodes, edges


def _infer_table_edges(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    valid = {node["id"] for node in nodes}
    edges = []
    for node in nodes:
        raw = node.get("raw") or {}
        text = " ".join(str(raw.get(key) or "") for key in ("desc", "fields", "columns"))
        for target in valid:
            if target == node["id"]:
                continue
            if f"{target}_id" in text.lower():
                edges.append({"source": node["id"], "target": target, "text": "关联"})
    for node in nodes:
        node.pop("raw", None)
    return edges[:20]


def _context(paper, design, chapters) -> Dict[str, Any]:
    return {
        "title": paper.title,
        "techs": _techs(paper),
        "modules": _modules(design)[:10],
        "features": _features(design)[:10],
        "tables": _tables(design)[:15],
        "chapters": [{"key": ch.key, "title": ch.title} for ch in (chapters or [])[:10]],
    }


def _classify_techs(techs: List[str]) -> Dict[str, List[str]]:
    grouped = {key: [] for key in [*TECH_GROUPS.keys(), "other"]}
    for tech in techs:
        normalized = str(tech).strip().lower()
        target = "other"
        for group, names in TECH_GROUPS.items():
            if normalized in names:
                target = group
                break
        grouped[target].append(str(tech).strip())
    return grouped


def _techs(paper) -> List[str]:
    aliases = {
        "springboot": "Spring Boot",
        "spring boot": "Spring Boot",
        "vue3": "Vue3",
        "vue": "Vue",
    }
    items = []
    for item in paper.techs or []:
        value = str(item).strip()
        if value:
            items.append(aliases.get(value.lower(), value))
    return items


def _modules(design) -> List[Dict[str, Any]]:
    return list(getattr(design, "modules", None) or [])


def _features(design) -> List[Dict[str, Any]]:
    return list(getattr(design, "features", None) or [])


def _tables(design) -> List[Dict[str, Any]]:
    return list(getattr(design, "tables", None) or [])


def _system_name(paper) -> str:
    title = re.sub(r"^基于.+?的", "", paper.title or "").strip("《》 ")
    return _short_text(title or "系统", 12)


def _join_role(items: List[str], role: str) -> str:
    label = " / ".join(items)
    return _short_text(f"{label} {role}", 16)


def _short_text(text: str, limit: int = 12) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    for sep in ["，", ",", "。", "；", ";", "、"]:
        if sep in cleaned:
            cleaned = cleaned.split(sep)[0]
    return cleaned[:limit].strip() or "节点"


def _er_text(text: str) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if len(lines) >= 2:
        return (lines[0][:14] + "\n" + lines[1][:24]).strip()
    return _short_text(text, 24)


def _safe_id(value: str, fallback: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9_\-\u4e00-\u9fff]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_-")
    return text or fallback


def _unique_id(value: str, used: set[str]) -> str:
    if value not in used:
        return value
    index = 2
    while f"{value}_{index}" in used:
        index += 1
    return f"{value}_{index}"
