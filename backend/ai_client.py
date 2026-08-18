# -*- coding: utf-8 -*-
"""PaperForge V0 可选 DeepSeek 接入:配置密钥后走真实 AI,失败自动降级。"""

import os
import re

from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

DEFAULT_MODEL = "deepseek-chat"


def ai_available():
    return OpenAI is not None and bool(os.environ.get("DEEPSEEK_API_KEY"))


def _client():
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )


def chat_json(system, user, retries=2):
    """返回解析后的 dict/list,失败返回 None。"""
    for _ in range(retries + 1):
        try:
            text = _chat(system, user)
            cleaned = text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.S)
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start : end + 1]
            import json

            return json.loads(cleaned)
        except Exception:
            continue
    return None


def chat_md(system, user, retries=2):
    """返回 Markdown 文本,失败返回 None。"""
    for _ in range(retries + 1):
        try:
            return _chat(system, user).strip()
        except Exception:
            continue
    return None


def suggest_topics_ai(keywords, techs, count=4, batch=0):
    """用 DeepSeek 生成题目建议;失败返回 None,由调用方降级为本地模板。"""
    system = "你是毕业设计选题规划助手,只输出合法 JSON,不输出其他内容。"
    user = (
        "研究方向关键词:%s\n可选技术栈:%s\n当前批次:%d\n"
        "请给出 %d 个差异明显、可落地的毕业设计题目建议,输出 JSON:\n"
        '{"topics":[{"title":"题目全称","techs":["技术1","技术2"],"description":"一句话亮点与理由","tags":["标签1","标签2"]}]}\n'
        "要求:题目贴合研究方向;techs 必须从可选技术栈中选择;不同批次之间题目不要重复。"
        % (keywords or "智慧校园综合管理", ", ".join(techs), batch, count)
    )
    data = chat_json(system, user)
    if not isinstance(data, dict) or not isinstance(data.get("topics"), list):
        return None
    topics = []
    for item in data["topics"]:
        if not isinstance(item, dict) or not str(item.get("title", "")).strip():
            continue
        topics.append(
            {
                "title": str(item["title"]).strip(),
                "techs": [str(t) for t in item.get("techs", []) if str(t).strip()][:4] or techs[:4],
                "description": str(item.get("description", "")).strip(),
                "tags": [str(t) for t in item.get("tags", []) if str(t).strip()][:3],
            }
        )
        if len(topics) >= count:
            break
    return topics or None


def _chat(system, user):
    client = _client()
    resp = client.chat.completions.create(
        model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.8,
        max_tokens=4096,
    )
    return resp.choices[0].message.content


def generate_paper_ai(title, techs, level="medium", style="严谨学术"):
    """用 DeepSeek 生成系统设定与各章节;任何一步失败返回 None,由调用方降级模板。"""
    design = _ai_system_design(title, techs)
    if not design:
        return None
    chapters = []
    order = [
        ("summary", "摘要与关键词", "中文摘要(约300字)与关键词"),
        ("abstract", "Abstract", "英文摘要与Keywords"),
        ("ch1", "第 1 章 绪论", "研究背景与意义、国内外研究现状、主要研究内容、论文组织结构"),
        ("ch2", "第 2 章 相关技术介绍", "逐项介绍所选技术栈,每项一小节"),
        ("ch3", "第 3 章 系统需求分析", "可行性分析、功能需求(列出全部模块)、非功能需求;在功能需求末尾插入:【此处建议插入:图 3-1 系统用例图】(素材:角色与功能描述文字)"),
        ("ch4", "第 4 章 系统设计", "总体架构、功能模块、数据库设计(列出全部数据表)、接口设计;分别插入【此处建议插入:图 4-1 系统架构图】、【此处建议插入:图 4-2 功能模块图】、【此处建议插入:图 4-3 E-R 图】"),
        ("ch5", "第 5 章 系统实现", "开发环境表格、关键模块实现、核心代码逻辑;末尾插入【此处建议插入:图 5-1 核心业务流程图】"),
        ("ch6", "第 6 章 系统测试", "测试环境、功能测试用例表格、测试结论"),
        ("ch7", "第 7 章 总结与展望", "工作总结、不足与展望"),
        ("refs", "参考文献与致谢", "参考文献5条以上(GB/T 7714格式)与致谢"),
    ]
    previous_summary = []
    for seq, (key, title_, hint) in enumerate(order):
        ctx = "\n".join(previous_summary[-3:])
        content = chat_md(
            "你是一名计算机毕业设计写作助手,负责撰写结构规范、表述严谨的中文论文初稿。"
            "所有章节必须严格使用给定的系统设定(模块、角色、数据表名称),不得自行改名或新增。",
            "论文题目:%s\n技术栈:%s\n字数档位:%s\n行文风格:%s\n\n系统设定:\n%s\n\n"
            "前文要点:\n%s\n\n请撰写「%s」,要求:%s。使用 Markdown 格式,"
            "章节内用 ## 二级标题,列表用 - 或 1.,不要输出最外层的一级标题。"
            % (
                title,
                ", ".join(techs),
                level,
                style,
                str(design),
                ctx,
                title_,
                hint,
            ),
        )
        if not content:
            return None
        chapters.append({"seq": seq, "key": key, "title": title_, "content_md": content})
        previous_summary.append("%s:前3行要点 %s" % (title_, content.splitlines()[0][:80]))

    full_md = "\n\n".join(
        "# %s\n\n%s" % (c["title"], c["content_md"]) if c["seq"] > 1 else c["content_md"]
        for c in chapters
    )
    words = len(full_md.replace("\n", "").replace(" ", ""))
    from .template_engine import chart_suggestions

    return {
        "title": title,
        "techs": techs,
        "level": level,
        "style": style,
        "system_design": design,
        "chapters": chapters,
        "chart_suggestions": chart_suggestions(),
        "stats": {"word_count": words},
        "mode": "ai",
    }


def _ai_system_design(title, techs):
    design = chat_json(
        "你是计算机毕业设计需求分析助手,只输出合法 JSON,不输出其他内容。",
        "论文题目:%s\n技术栈:%s\n请推导系统设定,输出 JSON 格式:\n"
        '{"modules":[{"name":"模块名","desc":"模块说明"}],"roles":["角色1","角色2"],'
        '"tables":[{"name":"表名","title":"中文表名","desc":"字段与用途说明"}],'
        '"features":[{"module":"模块名","desc":"功能说明"}],"domain_note":"一句话领域说明"}\n'
        "要求:模块 6-8 个,表 8-12 张,名称全篇统一。" % (title, ", ".join(techs)),
    )
    if not isinstance(design, dict):
        return None
    for key in ("modules", "roles", "tables", "features"):
        if not isinstance(design.get(key), list) or not design[key]:
            return None
    return design
