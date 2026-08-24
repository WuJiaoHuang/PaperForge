# -*- coding: utf-8 -*-
"""PaperForge 图表引擎:先规范化素材(AI 或本地解析),再按结构数据绘制,避免提示词混入图。"""

import io
import math
import re
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch

_CN_FONT = None
for _f in font_manager.fontManager.ttflist:
    if _f.name in ("SimHei", "Microsoft YaHei"):
        _CN_FONT = _f.name
        break
plt.rcParams["font.sans-serif"] = [_CN_FONT or "Microsoft YaHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

CHART_TYPES = {
    "er": {"label": "E-R 图", "hint": "粘贴 SQL 建表语句(CREATE TABLE …),留空则使用系统设定的数据表"},
    "flow": {"label": "流程图", "hint": "按顺序描述步骤,每行一步;留空则生成默认业务流程"},
    "architecture": {"label": "系统架构图", "hint": "粘贴分层说明,每行一层(如:用户层:浏览器);留空则按技术栈生成"},
    "module": {"label": "功能模块图", "hint": "可留空,默认使用系统设定的功能模块"},
    "usecase": {"label": "系统用例图", "hint": "可留空,默认使用系统设定的角色与功能"},
    "sequence": {"label": "时序图", "hint": "每行格式:角色A -> 角色B: 消息;留空则生成默认交互时序"},
}

BLUE = "#1e3a5f"
BLUE_LIGHT = "#eef3f8"
GOLD = "#a67c2e"
GOLD_LIGHT = "#f7f1e2"
GRAY = "#5f6b7a"

_SKIP_MARKERS = ("请根据", "绘制", "论文题目", "以下", "用于生成", "可直接", "技术栈:", "层次:", "系统功能模块:", "功能:", "角色:")


def _canvas(title, h=7.0, ylim=72):
    fig = plt.figure(figsize=(10, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, ylim)
    fig.suptitle(title or "", fontsize=15, fontweight="bold", color=BLUE, y=0.97)
    return fig, ax


def _rect(ax, x, y, w, h, text, fc=BLUE_LIGHT, ec=BLUE, fs=10, bold=False, lw=1.3,
          rounded=True, zorder=3, tc="#22262b"):
    style = "round,pad=0.3,rounding_size=1.2" if rounded else "square,pad=0.2"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, linewidth=lw,
                                edgecolor=ec, facecolor=fc, zorder=zorder))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, linespacing=1.35, zorder=zorder + 0.1)


def _arrow(ax, p1, p2, color=BLUE, lw=1.8, mutation=18):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=mutation,
                                 linewidth=lw, color=color, zorder=5))


def _line(ax, p1, p2, color=GRAY, lw=1.1, ls="-", zorder=2):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=lw, linestyle=ls, zorder=zorder)


def _actor(ax, x, y, label):
    ax.add_patch(plt.Circle((x, y + 1.9), 1.5, fill=False, lw=1.3, ec=BLUE, zorder=4))
    ax.plot([x, x], [y + 0.4, y - 2.6], color=BLUE, lw=1.3, zorder=4)
    ax.plot([x - 2.0, x + 2.0], [y - 0.6, y - 0.6], color=BLUE, lw=1.3, zorder=4)
    ax.plot([x, x - 1.8], [y - 2.6, y - 4.6], color=BLUE, lw=1.3, zorder=4)
    ax.plot([x, x + 1.8], [y - 2.6, y - 4.6], color=BLUE, lw=1.3, zorder=4)
    ax.text(x, y - 6.2, label, ha="center", fontsize=9, fontweight="bold", color=BLUE, zorder=4)


def _ellipse(ax, cx, cy, w, h, text, fc=BLUE_LIGHT, ec=BLUE, fs=8):
    ax.add_patch(Ellipse((cx, cy), w, h, facecolor=fc, edgecolor=ec, lw=1.3, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, zorder=4)


def _finalize(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def render_plantuml(source):
    """用本地 PlantUML(java + graphviz)把标准代码渲染成 PNG;失败返回 None。"""
    jar = Path(__file__).resolve().parents[2] / "deps" / "plantuml.jar"
    if not jar.exists():
        return None
    try:
        proc = subprocess.run(
            ["java", "-Dfile.encoding=UTF-8", "-jar", str(jar), "-pipe", "-tpng", "-charset", "UTF-8"],
            input=source.encode("utf-8"),
            capture_output=True,
            timeout=90,
        )
        if proc.returncode == 0 and proc.stdout and len(proc.stdout) > 200 and not proc.stderr.strip():
            return proc.stdout
    except Exception:
        return None
    return None


# ---------- 规范化解析(本地兜底,自动剔除说明性文字) ----------

def _clean_lines(material):
    out = []
    for line in (material or "").splitlines():
        line = line.strip().strip("-•*").strip()
        if not line:
            continue
        if any(m in line for m in _SKIP_MARKERS):
            continue
        out.append(line)
    return out


def _parse_sql_tables(material):
    tables = []
    for m in re.finditer(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?\s*\((.*?)\)\s*;",
        material or "",
        re.S | re.I,
    ):
        name = m.group(1)
        fields = []
        for line in m.group(2).splitlines():
            line = line.strip().rstrip(",").strip()
            if not line or line.upper().startswith(
                ("PRIMARY", "FOREIGN", "KEY", "UNIQUE", "INDEX", "CONSTRAINT", "CHECK", ")")
            ):
                continue
            fm = re.match(r"^`?(\w+)`?\s+(\w+)", line)
            fields.append("%s %s" % (fm.group(1), fm.group(2)) if fm else line[:20])
        tables.append((name, fields[:6]))
    return tables


def _design_tables(design):
    if not isinstance(design, dict):
        return []
    out = []
    for t in design.get("tables", []):
        if isinstance(t, dict):
            out.append((t.get("name") or t.get("title") or "表", [t.get("title") or "", t.get("desc") or ""]))
    return out


def _match_table(tables, prefix):
    for name, _f in tables:
        if name == prefix or name.endswith(prefix) or prefix in name:
            return name
    return None


def _table_relations(tables):
    rels = []
    for src, fields in tables:
        for f in fields:
            m = re.match(r"(\w+)_id\b", f)
            if not m or m.group(1) == "id":
                continue
            tgt = _match_table(tables, m.group(1))
            if tgt and tgt != src:
                rels.append((src, tgt))
    return rels


def _parse_local_er(material, design):
    tables = _parse_sql_tables(material) or _design_tables(design)
    if not tables:
        tables = [("业务表", ["id BIGINT"])]
    entities = [{"name": n, "fields": f} for n, f in tables[:12]]
    relations = [{"from": a, "to": b, "type": "N:1"} for a, b in _table_relations(tables)]
    if not relations and len(entities) > 1:
        relations = [{"from": e["name"], "to": entities[0]["name"], "type": "关联"} for e in entities[1:]]
    return {"entities": entities, "relations": relations}


def _parse_local_flow(material, design):
    steps = []
    for line in _clean_lines(material):
        if "->" in line:
            for part in line.split("->"):
                part = part.split(":")[0].strip()
                if part and part not in steps:
                    steps.append(part)
        else:
            part = line.split(":")[0].strip()
            if part and part not in steps:
                steps.append(part)
    if not steps:
        steps = ["开始", "用户登录系统", "用户发起业务请求", "系统保存数据并返回结果", "结束"]
    nodes = steps[:8]
    return {"nodes": nodes, "edges": [[i, i + 1] for i in range(len(nodes) - 1)]}


def _parse_local_architecture(material, design, techs):
    layers = []
    for line in (material or "").splitlines():
        line = line.strip()
        if not line or any(m in line for m in _SKIP_MARKERS):
            continue
        if ":" in line:
            name, _, detail = line.partition(":")
            layers.append({"name": name.strip(), "detail": detail.strip()})
        else:
            layers.append({"name": line, "detail": ""})
    if not layers:
        t = techs or []
        front = next((x for x in t if any(k in x for k in ("Vue", "React", "Element", "小程序"))), "前端框架")
        back = next((x for x in t if any(k in x for k in ("Spring", "Django", "Flask", "Node"))), "后端服务")
        db = next((x for x in t if "SQL" in x or "MySQL" in x), "关系数据库")
        cache = next((x for x in t if "Redis" in x), "")
        layers = [
            {"name": "用户层", "detail": "浏览器 / 小程序客户端"},
            {"name": "前端展示层", "detail": front},
            {"name": "业务逻辑层", "detail": back},
            {"name": "数据存储层", "detail": db + ((" / " + cache) if cache else "")},
        ]
    return {"layers": layers[:6]}


def _parse_local_module(material, design, title):
    modules = []
    for line in _clean_lines(material):
        if ":" in line:
            line = line.split(":", 1)[0].strip()
        if line:
            modules.append(line[:14])
    if not modules and isinstance(design, dict):
        modules = [m.get("name") for m in design.get("modules", []) if isinstance(m, dict) and m.get("name")]
    modules = [m for m in modules if m][:8]
    return {"root": (title or "系统")[:14], "modules": modules or ["用户管理", "业务管理", "系统管理"]}


def _parse_local_usecase(material, design, title):
    roles = []
    features = []
    for line in (material or "").splitlines():
        line = line.strip()
        if line.startswith("角色:"):
            roles = [r.strip() for r in line[3:].replace("，", "、").split("、") if r.strip()]
        elif line.startswith("-") or line.startswith("*"):
            f = line.lstrip("-* ").strip()
            if ":" in f:
                f = f.split(":", 1)[0].strip()
            if f:
                features.append(f[:10])
    if not roles:
        roles = [r for r in (design.get("roles", []) if isinstance(design, dict) else []) if r] or ["管理员", "普通用户"]
    if not features and isinstance(design, dict):
        for f in design.get("features", []):
            features.append((f.get("desc") if isinstance(f, dict) else str(f))[:10])
    roles = roles[:5]
    cases = []
    for i, f in enumerate(features[:8]):
        cases.append({"name": f, "actors": [roles[i % len(roles)]]})
    return {"system": ((title or "系统") + "系统")[:16], "actors": roles, "use_cases": cases or [{"name": "登录", "actors": [roles[0]]}]}


def _parse_local_sequence(material, design):
    msgs = []
    for line in (material or "").splitlines():
        line = line.strip()
        if not line or "->" not in line:
            continue
        a, rest = line.split("->", 1)
        b, _, msg = rest.partition(":")
        msgs.append({"from": a.strip(), "to": b.strip(), "label": msg.strip()})
    if not msgs:
        msgs = [
            {"from": "用户", "to": "系统", "label": "提交请求"},
            {"from": "系统", "to": "数据库", "label": "读写数据"},
            {"from": "系统", "to": "用户", "label": "返回结果"},
        ]
    actors = []
    for m in msgs:
        for x in (m["from"], m["to"]):
            if x not in actors:
                actors.append(x)
    return {"actors": actors[:6], "messages": msgs[:10]}


def build_spec(chart_type, material, design, techs, title):
    if chart_type == "er":
        return _parse_local_er(material, design)
    if chart_type == "flow":
        return _parse_local_flow(material, design)
    if chart_type == "architecture":
        return _parse_local_architecture(material, design, techs)
    if chart_type == "module":
        return _parse_local_module(material, design, title)
    if chart_type == "usecase":
        return _parse_local_usecase(material, design, title)
    if chart_type == "sequence":
        return _parse_local_sequence(material, design)
    return None


# ---------- 渲染 ----------

def _render_er(spec, title):
    entities = spec.get("entities") or [{"name": "业务表", "fields": ["id BIGINT"]}]
    relations = spec.get("relations") or []
    fig, ax = _canvas(title or "E-R 图", h=8.0, ylim=78)
    cx, cy, radius = 50, 40, 27
    pos = {}
    n = len(entities)
    for i, e in enumerate(entities[:12]):
        ang = math.pi / 2 + (2 * math.pi * i) / max(n, 2)
        pos[e["name"]] = (cx + radius * math.cos(ang), cy + radius * math.sin(ang))
    for rel in relations[:20]:
        a, b = rel.get("from"), rel.get("to")
        if a in pos and b in pos:
            x1, y1 = pos[a]
            x2, y2 = pos[b]
            _line(ax, (x1, y1), (x2, y2), color=GOLD, lw=1.5, ls="--", zorder=2)
            label = rel.get("type") or "关联"
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.3, label, ha="center",
                    fontsize=9, color=GOLD, fontweight="bold", zorder=4)
    for e in entities[:12]:
        x, y = pos[e["name"]]
        w = 34
        fields = e.get("fields") or []
        h = max(11, 5 + 1.6 * len(fields))
        bx, by = x - w / 2, y - h / 2
        _rect(ax, bx, by + h - 5, w, 5, e["name"][:10], fc=BLUE, ec=BLUE, fs=9,
              bold=True, rounded=False, zorder=3, tc="#ffffff")
        _rect(ax, bx, by, w, h - 5, "\n".join(fields[:6]), fc="#ffffff", ec=BLUE,
              fs=7.5, rounded=False, zorder=3)
    return _finalize(fig)


def _render_flow(spec, title):
    nodes = spec.get("nodes") or ["开始", "结束"]
    edges = spec.get("edges") or [[i, i + 1] for i in range(len(nodes) - 1)]
    fig, ax = _canvas(title or "核心业务流程图", h=8.5, ylim=78)
    n = len(nodes)
    box_h = 7
    gap = (72 - n * box_h) / (n + 1)
    xs, bw = 30, 40
    ys = {}
    for i, node in enumerate(nodes[:8]):
        y = 2 + gap * (i + 1) + i * box_h
        ys[i] = y
        _rect(ax, xs, y, bw, box_h, node[:16], fs=10, zorder=3)
    for a, b in edges:
        if a in ys and b in ys:
            _arrow(ax, (xs + bw / 2, ys[a] + box_h), (xs + bw / 2, ys[b]), lw=2.0, mutation=20)
    return _finalize(fig)


def _render_architecture(spec, title):
    layers = spec.get("layers") or [{"name": "用户层", "detail": ""}, {"name": "系统", "detail": ""}]
    fig, ax = _canvas(title or "系统架构图", h=8.0, ylim=82)
    n = len(layers[:6])
    band_h = 7
    gap = (74 - n * band_h) / (n + 1)
    ys = []
    for i, layer in enumerate(layers[:6]):
        name = layer.get("name", "")
        detail = layer.get("detail", "")
        text = (name + " · " + detail) if detail else name
        y = 3 + gap * (i + 1) + i * band_h
        ys.append(y)
        _rect(ax, 20, y, 60, band_h, text[:22], fs=11, bold=True, zorder=3)
        if i > 0:
            _arrow(ax, (50, ys[i - 1] + band_h), (50, y), lw=2.0, mutation=20)
    return _finalize(fig)


def _render_module(spec, title):
    root = (spec.get("root") or title or "系统")[:14]
    modules = spec.get("modules") or ["用户管理", "业务管理", "系统管理"]
    fig, ax = _canvas(title or "功能模块图", h=6.5, ylim=64)
    root_x, root_w, root_h = 50, 36, 6
    root_y = 52
    _rect(ax, root_x - root_w / 2, root_y, root_w, root_h, root, fc=GOLD_LIGHT,
          ec=GOLD, fs=11, bold=True, zorder=3)
    n = len(modules[:8])
    spacing = 88 / max(n, 1)
    for i, name in enumerate(modules[:8]):
        x = 6 + spacing * i + spacing / 2
        bw = min(spacing - 5, 26)
        bh = 10
        _rect(ax, x - bw / 2, 28, bw, bh, name[:10], fs=9, zorder=3)
        _arrow(ax, (root_x, root_y), (x, 28 + bh), lw=1.6, mutation=16)
    return _finalize(fig)


def _render_usecase(spec, title):
    actors = spec.get("actors") or ["管理员", "普通用户"]
    cases = spec.get("use_cases") or [{"name": "登录", "actors": [actors[0]]}]
    system = (spec.get("system") or title or "系统")[:16]
    fig, ax = _canvas(title or "系统用例图", h=7.5, ylim=76)
    bx, by, bw, bh = 28, 8, 68, 60
    ax.add_patch(FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.3,rounding_size=1.2",
                                linewidth=1.4, edgecolor=GRAY, facecolor="none",
                                linestyle="--", zorder=1))
    ax.text(bx + 2, by + bh - 2, system, fontsize=11, fontweight="bold", color=GRAY,
            ha="left", va="top", zorder=2)
    for i, r in enumerate(actors[:5]):
        _actor(ax, 12, 56 - i * 10, r)
    ncols = 2
    for i, c in enumerate(cases[:8]):
        col = i % ncols
        row = i // ncols
        cx = 40 + col * 25
        cy = by + bh - 14 - row * 12
        _ellipse(ax, cx, cy, 23, 9, (c.get("name") or "")[:10], fs=8)
    for i, c in enumerate(cases[:8]):
        col = i % ncols
        row = i // ncols
        cx = 40 + col * 25
        cy = by + bh - 14 - row * 12
        for a in (c.get("actors") or [actors[i % len(actors)]])[:2]:
            ai = actors.index(a) if a in actors else i % len(actors)
            ay = 56 - ai * 10 - 3
            _line(ax, (14, ay), (cx - 11.5, cy), color=GRAY, lw=1.1)
    return _finalize(fig)


def _render_sequence(spec, title):
    actors = spec.get("actors") or ["用户", "系统", "数据库"]
    messages = spec.get("messages") or []
    fig, ax = _canvas(title or "时序图", h=7.0, ylim=70)
    n = max(len(actors), 2)
    xs = {name: 18 + i * (64 / (n - 1)) for i, name in enumerate(actors)}
    for name in actors:
        x = xs[name]
        _rect(ax, x - 9, 60, 18, 5, name[:8], fs=9, bold=True, zorder=3)
        ax.plot([x, x], [3, 60], color=GRAY, lw=0.9, ls="--", zorder=2)
    y = 54
    for m in messages[:10]:
        a, b = m.get("from"), m.get("to")
        if a in xs and b in xs:
            _arrow(ax, (xs[a], y), (xs[b], y), lw=1.6, mutation=16)
            label = m.get("label") or ""
            if label:
                ax.text((xs[a] + xs[b]) / 2, y + 1.4, label[:16], ha="center",
                        va="bottom", fontsize=8, color=BLUE, zorder=4)
            y -= 5.0
    return _finalize(fig)


def generate_chart_bytes(chart_type, title, material, design=None, techs=None, spec=None, plantuml_src=None):
    if plantuml_src:
        png = render_plantuml(plantuml_src)
        if png:
            return io.BytesIO(png)
    if spec is None:
        spec = build_spec(chart_type, material, design, techs, title)
    if spec is None:
        return None
    if chart_type == "er":
        return _render_er(spec, title)
    if chart_type == "flow":
        return _render_flow(spec, title)
    if chart_type == "architecture":
        return _render_architecture(spec, title)
    if chart_type == "module":
        return _render_module(spec, title)
    if chart_type == "usecase":
        return _render_usecase(spec, title)
    if chart_type == "sequence":
        return _render_sequence(spec, title)
    return None


# ---------- 规范化默认素材(提示词) ----------

def _er_sql(design):
    tables = design.get("tables", []) if isinstance(design, dict) else []
    if not tables:
        return ""
    first_name = None
    first_title = None
    out = ["-- 数据库表结构(SQL 建表语句,可直接用于生成 E-R 图)", ""]
    picked = tables[:12]
    for i, t in enumerate(picked):
        name = t.get("name") if isinstance(t, dict) else ""
        title = (t.get("title") if isinstance(t, dict) else "") or name
        name = name or ("table_%d" % (i + 1))
        if i == 0:
            first_name = name
            first_title = title
        out.append("-- %s" % title)
        out.append("CREATE TABLE %s (" % name)
        out.append("  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',")
        out.append("  name VARCHAR(50) NOT NULL COMMENT '名称',")
        if first_name and name != first_name:
            fk = first_name[4:] if first_name.startswith("sys_") else first_name
            out.append("  %s_id BIGINT COMMENT '关联%s'," % (fk, first_title or "主表"))
        out.append("  status INT DEFAULT 1 COMMENT '状态:1正常 0停用',")
        out.append("  remark VARCHAR(200) COMMENT '备注',")
        out.append("  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'")
        out.append(");")
        if i < len(picked) - 1:
            out.append("")
    return "\n".join(out)


def _flow_steps(design):
    steps = ["开始", "用户登录系统"]
    if isinstance(design, dict):
        for f in design.get("features", [])[:4]:
            if isinstance(f, dict):
                steps.append(str(f.get("module") or "业务处理")[:18])
            else:
                steps.append(str(f).split(":")[0][:18])
    if len(steps) == 2:
        steps.append("用户发起业务请求")
    steps += ["系统保存数据并返回结果", "结束"]
    return "\n".join(steps)


def _architecture_layers(techs):
    techs = techs or []

    def pick(*kws, default=""):
        for t in techs:
            if any(k.lower() in str(t).lower() for k in kws):
                return str(t)
        return default

    front = pick("Vue", "React", "Element", "小程序", default="前端框架")
    back = pick("SpringBoot", "Spring", "SSM", "Django", "Flask", "Node", default="后端服务")
    db = pick("MySQL", "Oracle", "SQLServer", "PostgreSQL", default="关系数据库")
    cache = pick("Redis", default="")
    return "\n".join(
        [
            "用户层:浏览器 / 小程序客户端",
            "前端展示层:%s" % front,
            "业务逻辑层:%s" % back,
            "数据存储层:%s%s" % (db, (" / %s" % cache) if cache else ""),
        ]
    )


def _module_list(design):
    modules = []
    if isinstance(design, dict):
        modules = [m.get("name") for m in design.get("modules", []) if isinstance(m, dict) and m.get("name")]
    modules = modules[:12] or ["用户管理", "业务管理", "系统管理"]
    return "\n".join(["系统功能模块:"] + ["- %s" % m for m in modules])


def _usecase_text(design):
    roles = design.get("roles", []) if isinstance(design, dict) else []
    features = []
    if isinstance(design, dict):
        for f in design.get("features", []):
            if isinstance(f, dict):
                features.append((f.get("module") or "") + ":" + (f.get("desc") or ""))
            else:
                features.append(str(f))
    out = ["角色:" + ("、".join(roles) if roles else "管理员、普通用户")]
    if features:
        out.append("功能:")
        out += ["- %s" % f for f in features[:12]]
    return "\n".join(out)


def _sequence_text(design):
    return "\n".join(
        [
            "用户 -> 系统: 提交登录请求",
            "系统 -> 数据库: 查询业务数据",
            "数据库 -> 系统: 返回数据结果",
            "系统 -> 用户: 返回处理结果",
        ]
    )


def build_chart_prompt(chart_type, design, techs, title):
    """根据论文上下文生成规范化默认素材(提示词)。"""
    if chart_type == "er":
        sql = _er_sql(design)
        return sql or "请提供 SQL 建表语句(CREATE TABLE …),用于生成 E-R 图。"
    if chart_type == "flow":
        return "请根据以下业务流程绘制流程图。\n论文题目:%s\n%s" % (title or "论文", _flow_steps(design))
    if chart_type == "architecture":
        return "请根据以下技术栈绘制系统架构图。\n技术栈:%s\n%s" % (
            "、".join(techs) if techs else "系统技术栈",
            _architecture_layers(techs),
        )
    if chart_type == "module":
        return "请根据以下功能模块绘制功能模块图。\n论文题目:%s\n%s" % (title or "论文", _module_list(design))
    if chart_type == "usecase":
        return "请根据以下系统信息绘制系统用例图。\n系统名称:%s\n%s" % (title or "系统", _usecase_text(design))
    if chart_type == "sequence":
        return "请根据以下交互流程绘制时序图。\n论文题目:%s\n%s" % (title or "论文", _sequence_text(design))
    return ""
