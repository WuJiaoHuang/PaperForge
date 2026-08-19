# -*- coding: utf-8 -*-
"""PaperForge V0 可选 DeepSeek 接入:配置密钥后走真实 AI,失败自动降级。"""

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

DEFAULT_MODEL = "deepseek-chat"

CHAPTER_ORDER = [
    ("summary", "摘要与关键词", "中文摘要(约300字)与关键词"),
    ("abstract", "Abstract", "英文摘要与Keywords"),
    ("ch1", "第 1 章 绪论", "研究背景与意义、国内外研究现状、主要研究内容、论文组织结构"),
    ("ch2", "第 2 章 相关技术介绍", "逐项介绍所选技术栈,每项一小节"),
    ("ch3", "第 3 章 系统需求分析", "可行性分析、功能需求(列出全部模块)、非功能需求;在功能需求末尾插入:【此处建议插入:图 3-1 系统用例图(需标注系统角色)】"),
    ("ch4", "第 4 章 系统设计", "总体架构、功能模块、数据库设计(列出全部数据表)、接口设计;分别插入【此处建议插入:图 4-1 系统架构图(需标注所用技术栈)】、【此处建议插入:图 4-2 功能模块图】、【此处建议插入:图 4-3 E-R 图】"),
    ("ch5", "第 5 章 系统实现", "开发环境表格、关键模块实现、核心代码逻辑;末尾插入【此处建议插入:图 5-1 核心业务流程图】"),
    ("ch6", "第 6 章 系统测试", "测试环境、功能测试用例表格、测试结论"),
    ("ch7", "第 7 章 总结与展望", "工作总结、不足与展望"),
    ("refs", "参考文献与致谢", "参考文献5条以上(GB/T 7714格式)与致谢"),
]


def ai_available():
    return OpenAI is not None and bool(os.environ.get("DEEPSEEK_API_KEY"))


def _client():
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        timeout=120.0,
        max_retries=1,
    )


def chat_json(system, user, retries=1, max_tokens=4096, temperature=0.8):
    """返回解析后的 dict/list,失败返回 None。"""
    for _ in range(retries + 1):
        try:
            text = _chat(system, user, max_tokens=max_tokens, temperature=temperature)
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


def chat_md(system, user, retries=1, max_tokens=4096, temperature=0.8):
    """返回 Markdown 文本,失败返回 None。"""
    for _ in range(retries + 1):
        try:
            return _chat(system, user, max_tokens=max_tokens, temperature=temperature).strip()
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
    data = chat_json(system, user, max_tokens=1500, temperature=0.6)
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


def _design_context(design, techs, title):
    if not isinstance(design, dict):
        return "技术栈:%s" % "、".join(techs or [])
    parts = []
    if design.get("modules"):
        parts.append("模块:" + "、".join(m.get("name") for m in design["modules"][:8] if isinstance(m, dict)))
    if design.get("roles"):
        parts.append("角色:" + "、".join(design["roles"]))
    if design.get("tables"):
        parts.append("数据表:" + "、".join((t.get("name") or "") for t in design["tables"][:10] if isinstance(t, dict)))
    parts.append("技术栈:" + "、".join(techs or []))
    return "; ".join(parts)


CHART_SPEC_SCHEMAS = {
    "er": '{"entities":[{"name":"实体名","fields":["字段1","字段2"]}],"relations":[{"from":"实体A","to":"实体B","type":"1:N"}]}',
    "flow": '{"nodes":["开始","步骤1","结束"],"edges":[[0,1],[1,2]]}',
    "architecture": '{"layers":[{"name":"用户层","detail":"浏览器 / 小程序"}]}',
    "module": '{"root":"系统名称","modules":["模块1","模块2"]}',
    "usecase": '{"system":"系统名称","actors":["角色1"],"use_cases":[{"name":"用例名","actors":["角色1"]}]}',
    "sequence": '{"actors":["角色1","角色2"],"messages":[{"from":"角色1","to":"角色2","label":"消息"}]}',
}


def parse_chart_spec_ai(chart_type, material, design, title, techs):
    """用 DeepSeek 把图表素材转换成规范化绘图数据;失败返回 None。"""
    schema = CHART_SPEC_SCHEMAS.get(chart_type)
    if not schema:
        return None
    system = "你是绘图数据转换助手,只输出合法 JSON,不输出其他内容。"
    user = (
        "请把下面的素材转换成绘制%s所需的规范化 JSON 数据。\n"
        "论文题目:%s\n系统设定:%s\n\n素材内容:\n%s\n\n"
        "要求:忽略'请根据…绘制…''论文题目:''技术栈:'等说明性、指示性文字,只保留真实图形要素;"
        "关系与连线只根据素材明确表达的内容生成,不要臆造;按如下 JSON 结构输出,不要输出其他内容:\n%s"
        % (chart_type, title or "", _design_context(design, techs, title), material or "", schema)
    )
    data = chat_json(system, user, max_tokens=1200, temperature=0.3)
    if not isinstance(data, dict):
        return None
    return data


PLANTUML_GUIDES = {
    "er": (
        "E-R 图(entity 语法):\n@startuml\nhide circle\n"
        'entity "sys_user" as user {\n  * id : BIGINT <<PK>>\n  --\n  name : VARCHAR\n}\n'
        'entity "orders" as orders {\n  * id : BIGINT <<PK>>\n  --\n  user_id : BIGINT\n}\n'
        "user ||--o{ orders\n@enduml"
    ),
    "flow": (
        "流程图(activity 语法):\n@startuml\nstart\n:用户登录系统;\n:浏览商品;\n"
        "if (库存充足?) then (是)\n  :创建订单;\nelse (否)\n  :提示无货;\nendif\nstop\n@enduml"
    ),
    "architecture": (
        "系统架构图(component 语法):\n@startuml\n[用户层:浏览器 / 小程序] --> [前端展示层:Vue]\n"
        "[前端展示层:Vue] --> [业务逻辑层:Spring Boot]\n[业务逻辑层:Spring Boot] --> [数据存储层:MySQL / Redis]\n@enduml"
    ),
    "module": (
        "功能模块图(component 树形):\n@startuml\n[系统] --> [用户管理]\n[系统] --> [商品管理]\n[系统] --> [订单管理]\n@enduml"
    ),
    "usecase": (
        "系统用例图(usecase 语法,必须用 rectangle 画出系统边界并写上系统名称):\n@startuml\nleft to right direction\n"
        'actor "管理员" as a1\nactor "普通用户" as a2\nrectangle "校园二手交易平台" {\n'
        '  usecase "登录" as u1\n  usecase "商品管理" as u2\n}\na1 --> u2\na2 --> u1\n@enduml'
    ),
    "sequence": (
        "时序图(sequence 语法):\n@startuml\nactor 用户\nparticipant \"系统\" as sys\nparticipant \"数据库\" as db\n"
        "用户 -> sys: 提交请求\nsys -> db: 读写数据\ndb --> sys: 返回数据\nsys --> 用户: 返回结果\n@enduml"
    ),
}


def plantuml_chart_ai(chart_type, material, design, title, techs):
    """用 DeepSeek 生成标准 PlantUML 代码;失败返回 None。"""
    guide = PLANTUML_GUIDES.get(chart_type)
    if not guide:
        return None
    system = "你是专业的绘图代码生成助手,只输出 PlantUML 代码,不要输出其他任何文字。"
    user = (
        "请根据以下素材与系统信息,生成%s 的 PlantUML 代码。\n"
        "论文题目:%s\n系统设定:%s\n\n素材内容:\n%s\n\n语法参考示例:\n%s\n\n"
        "要求:忽略'请根据…绘制…''论文题目:''技术栈:'等说明性文字,只保留真实图形要素;"
        "关系与连线只根据素材明确表达的内容生成,不要臆造;用例图必须用 rectangle 写出系统名称。"
        "直接输出 @startuml 开头、@enduml 结尾的完整 PlantUML 代码。"
        % (chart_type, title or "", _design_context(design, techs, title), material or "", guide)
    )
    return chat_md(system, user, max_tokens=1600, temperature=0.2)


def _chat(system, user, max_tokens=4096, temperature=0.8):
    client = _client()
    resp = client.chat.completions.create(
        model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def generate_paper_ai(title, techs, level="medium", style="严谨学术", requirements="", on_stage=None, on_chapter=None, on_design=None):
    """用 DeepSeek 生成系统设定与各章节;任何一步失败返回 None,由调用方降级模板。

    on_stage(current, total, stage_name) 用于汇报生成进度(系统设定 1 步 + 章节 10 步)。
    on_chapter(seq, key, title, content_md) 每完成一章回调一次,便于实时展示。
    on_design(design) 系统设定生成后回调。
    """
    if on_stage:
        on_stage(0, 11, "系统设定")
    design = _ai_system_design(title, techs, requirements)
    if not design:
        return None
    if on_design:
        on_design(design)
    order = CHAPTER_ORDER
    system_prompt = (
        "你是一名计算机毕业设计写作助手,负责撰写结构规范、表述严谨的中文论文初稿。"
        "所有章节必须严格使用给定的系统设定(模块、角色、数据表名称),不得自行改名或新增。"
    )
    req_line = ""
    if requirements and str(requirements).strip():
        req_line = "\n\n用户补充需求(必须落实到本部分内容中):%s" % str(requirements).strip()

    def build_one(item):
        seq, (key, title_, hint) = item
        content = chat_md(
            system_prompt,
            "论文题目:%s\n技术栈:%s\n字数档位:%s\n行文风格:%s\n\n系统设定:\n%s\n\n"
            "请撰写「%s」,要求:%s。使用 Markdown 格式,"
            "章节内用 ## 二级标题,列表用 - 或 1.,不要输出最外层的一级标题。%s"
            % (title, ", ".join(techs), level, style, str(design), title_, hint, req_line),
        )
        return seq, key, title_, hint, content

    total = len(order)
    results = {}
    numbered = list(enumerate(order))
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(build_one, (seq, inner)): seq for seq, inner in numbered}
        done = 0
        for fut in as_completed(futures):
            seq, key, title_, hint, content = fut.result()
            results[seq] = (key, title_, hint, content)
            done += 1
            if on_stage:
                on_stage(done, total, title_)
            if on_chapter and content:
                on_chapter(seq, key, title_, hint, content)

    if len(results) != total or any(content is None for _, _, _, content in results.values()):
        return None
    chapters = [
        {"seq": seq, "key": key, "title": title_, "content_md": content, "hint": hint}
        for seq, (key, title_, hint, content) in sorted(results.items())
    ]

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


def regenerate_chapter_ai(title, techs, level, style, design, key, chapter_title, hint, instructions="", requirements=""):
    """单独重新生成某一章;失败返回 None,由调用方降级模板。"""
    system_prompt = (
        "你是一名计算机毕业设计写作助手,负责撰写结构规范、表述严谨的中文论文初稿。"
        "所有章节必须严格使用给定的系统设定(模块、角色、数据表名称),不得自行改名或新增。"
    )
    prompt = (
        "论文题目:%s\n技术栈:%s\n字数档位:%s\n行文风格:%s\n\n系统设定:\n%s\n\n"
        "请撰写「%s」,要求:%s。使用 Markdown 格式,"
        "章节内用 ## 二级标题,列表用 - 或 1.,不要输出最外层的一级标题。"
        % (title, ", ".join(techs), level, style, str(design), chapter_title, hint)
    )
    if instructions and str(instructions).strip():
        prompt += "\n\n用户修改意见(必须认真遵循并落实到内容中):%s" % str(instructions).strip()
    if requirements and str(requirements).strip():
        prompt += "\n\n系统级补充需求(同样必须落实):%s" % str(requirements).strip()
    return chat_md(system_prompt, prompt)


def _ai_system_design(title, techs, requirements=""):
    req_line = ""
    if requirements and str(requirements).strip():
        req_line = "\n用户补充需求(必须体现到模块、角色与数据表设计中):%s" % str(requirements).strip()
    design = chat_json(
        "你是计算机毕业设计需求分析助手,只输出合法 JSON,不输出其他内容。",
        "论文题目:%s\n技术栈:%s\n请推导系统设定,输出 JSON 格式:\n"
        '{"modules":[{"name":"模块名","desc":"模块说明"}],"roles":["角色1","角色2"],'
        '"tables":[{"name":"表名","title":"中文表名","desc":"字段与用途说明"}],'
        '"features":[{"module":"模块名","desc":"功能说明"}],"domain_note":"一句话领域说明"}\n'
        "要求:模块 6-8 个,表 8-12 张,名称全篇统一。%s" % (title, ", ".join(techs), req_line),
    )
    if not isinstance(design, dict):
        return None
    for key in ("modules", "roles", "tables", "features"):
        if not isinstance(design.get(key), list) or not design[key]:
            return None
    return design
