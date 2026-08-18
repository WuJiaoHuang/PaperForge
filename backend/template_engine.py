# -*- coding: utf-8 -*-
"""PaperForge V0 本地模板引擎:根据题目与技术栈推导系统设定并生成论文初稿。"""

DOMAINS = [
    (
        ("商城", "电商", "购物", "交易", "二手", "拍卖", "团购", "外卖", "订餐"),
        {
            "roles": ["管理员", "普通用户", "商家/卖家"],
            "extra_modules": [
                ("商品管理", "商品信息发布、分类管理、上下架与库存维护"),
                ("购物车管理", "商品加入购物车、数量修改与批量结算"),
                ("订单管理", "订单创建、状态流转、发货与售后处理"),
                ("支付管理", "对接支付渠道,记录支付流水与退款"),
                ("评价管理", "订单完成后发表评价与回复"),
            ],
            "extra_tables": [
                ("goods", "商品信息表", "商品基本信息、价格、库存与上下架状态"),
                ("cart", "购物车表", "用户购物车中的商品与数量"),
                ("orders", "订单表", "订单编号、金额、状态与收货信息"),
                ("order_item", "订单明细表", "订单内商品的快照与数量"),
                ("payment", "支付记录表", "支付流水、金额、渠道与状态"),
                ("comment", "评价表", "用户对商品或订单的评价内容"),
            ],
        },
    ),
    (
        ("图书", "图书馆", "书城", "借阅"),
        {
            "roles": ["管理员", "读者"],
            "extra_modules": [
                ("图书管理", "图书信息录入、分类、上架与库存管理"),
                ("借阅管理", "借书、还书、续借与逾期处理"),
                ("读者管理", "读者信息维护与借阅证管理"),
                ("统计管理", "借阅量、热门图书与馆藏统计"),
            ],
            "extra_tables": [
                ("book", "图书信息表", "图书名称、作者、分类、库存"),
                ("reader", "读者信息表", "读者姓名、证件号、联系方式"),
                ("borrow", "借阅记录表", "借阅时间、应还时间、归还状态"),
            ],
        },
    ),
    (
        ("学生", "教务", "选课", "课程", "成绩", "教学"),
        {
            "roles": ["管理员", "教师", "学生"],
            "extra_modules": [
                ("学生管理", "学生信息录入、修改与查询"),
                ("教师管理", "教师信息维护与授课安排"),
                ("课程管理", "课程信息发布、选课人数控制"),
                ("选课管理", "学生选课、退课与选课名单查询"),
                ("成绩管理", "成绩录入、查询与统计分析"),
            ],
            "extra_tables": [
                ("student", "学生信息表", "学号、姓名、班级、联系方式"),
                ("teacher", "教师信息表", "工号、姓名、院系、联系方式"),
                ("course", "课程信息表", "课程名称、学分、容量、授课教师"),
                ("score", "成绩表", "学生、课程、成绩与录入时间"),
            ],
        },
    ),
    (
        ("社团", "协会", "活动报名"),
        {
            "roles": ["管理员", "社团负责人", "普通成员"],
            "extra_modules": [
                ("社团管理", "社团创建、资料维护与成员管理"),
                ("活动管理", "活动发布、报名与签到管理"),
                ("成员管理", "成员申请审核与角色分配"),
                ("通知管理", "社团公告与活动通知发布"),
            ],
            "extra_tables": [
                ("club", "社团信息表", "社团名称、简介、负责人"),
                ("activity", "活动信息表", "活动名称、时间、地点、报名人数"),
                ("club_member", "社团成员表", "成员、社团、加入时间、角色"),
            ],
        },
    ),
    (
        ("设备", "资产", "实验室", "机房"),
        {
            "roles": ["管理员", "普通用户"],
            "extra_modules": [
                ("设备管理", "设备信息登记、分类与状态管理"),
                ("借用管理", "设备借用申请、审批与归还"),
                ("维修管理", "设备报修、维修进度与记录"),
                ("统计报表", "设备使用率与借还统计"),
            ],
            "extra_tables": [
                ("device", "设备信息表", "设备编号、名称、类型、状态"),
                ("borrow_record", "借用记录表", "设备、借用人与时间"),
                ("repair_record", "维修记录表", "设备、故障描述与处理结果"),
            ],
        },
    ),
    (
        ("车辆", "汽修", "汽车", "4S", "停车"),
        {
            "roles": ["管理员", "客户", "技师"],
            "extra_modules": [
                ("车辆信息管理", "车辆档案、保险与年检信息维护"),
                ("维修管理", "维修工单、派工与进度跟踪"),
                ("客户管理", "客户信息与车辆绑定"),
                ("配件管理", "配件库存与出入库记录"),
            ],
            "extra_tables": [
                ("vehicle", "车辆信息表", "车牌、品牌、车主、里程"),
                ("customer", "客户信息表", "姓名、电话、地址"),
                ("repair_order", "维修工单表", "车辆、项目、费用、状态"),
                ("part", "配件表", "配件名称、库存、价格"),
            ],
        },
    ),
    (
        ("宿舍", "公寓", "入住"),
        {
            "roles": ["管理员", "学生", "宿管员"],
            "extra_modules": [
                ("宿舍管理", "宿舍楼栋、房间与床位管理"),
                ("入住管理", "学生入住、调宿与退宿办理"),
                ("报修管理", "宿舍设施报修与处理"),
                ("来访登记", "访客登记与查询"),
            ],
            "extra_tables": [
                ("dorm", "宿舍信息表", "楼栋、房间、床位与容量"),
                ("student", "学生信息表", "学号、姓名、班级"),
                ("checkin", "入住记录表", "学生、宿舍、入住与退宿时间"),
            ],
        },
    ),
    (
        ("医院", "门诊", "诊所", "患者", "挂号"),
        {
            "roles": ["管理员", "医生", "患者"],
            "extra_modules": [
                ("患者管理", "患者信息建档与维护"),
                ("挂号管理", "科室挂号、号源与候诊管理"),
                ("医生管理", "医生排班与出诊信息"),
                ("药品管理", "药品信息与库存管理"),
                ("就诊记录", "病历与就诊历史管理"),
            ],
            "extra_tables": [
                ("patient", "患者信息表", "姓名、证件、病史"),
                ("doctor", "医生信息表", "姓名、科室、职称"),
                ("registration", "挂号记录表", "患者、科室、医生、时间"),
                ("drug", "药品信息表", "药品名称、规格、库存"),
            ],
        },
    ),
    (
        ("酒店", "民宿", "客房", "预订"),
        {
            "roles": ["管理员", "前台", "客户"],
            "extra_modules": [
                ("客房管理", "房型、房间状态与价格管理"),
                ("预订管理", "在线预订、入住与退房办理"),
                ("客户管理", "客户信息与会员管理"),
                ("财务管理", "订单结算与账单查询"),
            ],
            "extra_tables": [
                ("room", "客房信息表", "房号、房型、状态、价格"),
                ("reservation", "预订记录表", "客户、房间、入住退房时间"),
                ("customer", "客户信息表", "姓名、电话、证件"),
            ],
        },
    ),
    (
        ("物流", "快递", "配送", "运单"),
        {
            "roles": ["管理员", "快递员", "客户"],
            "extra_modules": [
                ("运单管理", "运单创建、状态更新与查询"),
                ("网点管理", "网点信息与覆盖区域管理"),
                ("快递员管理", "快递员信息与派送任务分配"),
                ("客户管理", "寄件人与收件人信息维护"),
            ],
            "extra_tables": [
                ("waybill", "运单信息表", "运单号、寄收件人、状态"),
                ("branch", "网点信息表", "网点名称、地址、负责人"),
                ("courier", "快递员信息表", "姓名、电话、所属网点"),
            ],
        },
    ),
]

BASE_MODULES = [
    ("用户管理", "用户注册、登录、个人信息维护与权限控制"),
    ("系统管理", "角色权限配置、操作日志与系统参数维护"),
]

BASE_TABLES = [
    ("sys_user", "用户信息表", "登录账号、密码、角色与状态"),
    ("sys_role", "角色信息表", "角色名称、权限标识"),
    ("sys_log", "操作日志表", "操作人、操作内容与时间"),
]

TECH_MAP = {
    "SpringBoot": "Spring Boot 是当前 Java 领域主流的后端开发框架,基于 Spring 生态提供自动配置、内嵌服务器与起步依赖,能够显著降低项目搭建成本,便于快速构建稳定可靠的 Web 服务。",
    "Spring": "Spring 是 Java 平台的核心框架之一,通过控制反转与面向切面编程降低了业务代码的耦合度,为系统提供了良好的分层与扩展能力。",
    "SSM": "SSM 是 Spring、Spring MVC 与 MyBatis 的组合,是经典的 Java Web 开发架构,具有结构清晰、配置灵活、适合中小型系统开发的特点。",
    "MyBatis": "MyBatis 是一款轻量级的持久层框架,通过 XML 或注解将 SQL 与 Java 方法绑定,在保证灵活性的同时简化了数据库访问代码。",
    "MyBatis-Plus": "MyBatis-Plus 在 MyBatis 基础上提供了通用 CRUD、条件构造器与分页插件等能力,进一步减少了重复的数据库操作代码。",
    "Vue": "Vue.js 是一套渐进式前端框架,采用组件化开发与响应式数据绑定,配合 Element UI 等组件库可以高效搭建界面,并通过 Axios 与后端进行数据交互。",
    "Vue3": "Vue 3 引入了组合式 API 与更高效的响应式系统,配合 Element Plus 与 Vite,能够更灵活地组织前端代码,提升页面开发与维护效率。",
    "React": "React 是 Facebook 推出的前端框架,采用组件化与虚拟 DOM 技术,生态丰富,适合构建交互复杂、可复用程度高的用户界面。",
    "Element UI": "Element UI 是一套基于 Vue 的桌面端组件库,提供了表格、表单、弹窗等常用组件,能够显著提升后台管理页面的开发效率。",
    "Element Plus": "Element Plus 是 Vue 3 生态下的桌面端组件库,组件丰富、风格统一,广泛用于后台管理系统的界面开发。",
    "MySQL": "MySQL 是一款开源的关系型数据库管理系统,支持事务、索引与存储过程,具有性能稳定、使用广泛等特点,适合中小型业务系统的数据存储。",
    "Redis": "Redis 是一款高性能的键值存储系统,常用于缓存、会话管理与热点数据存储,能够有效提升系统的并发处理能力与响应速度。",
    "Python": "Python 语法简洁、生态丰富,在 Web 开发、数据分析与人工智能等领域应用广泛,是快速实现系统原型的常用语言。",
    "Django": "Django 是 Python 生态中成熟的全栈 Web 框架,自带 ORM、Admin 后台与安全机制,适合快速开发数据驱动的 Web 应用。",
    "Flask": "Flask 是一款轻量级的 Python Web 框架,核心简洁、扩展灵活,适合快速搭建接口服务与中小型应用。",
    "小程序": "微信小程序依托微信生态,无需安装即可使用,配合云开发能力可以快速实现移动端业务,是目前校园与生活服务类应用的主流载体之一。",
    "Node.js": "Node.js 基于 V8 引擎,采用事件驱动与非阻塞 I/O 模型,适合构建高并发的后端服务与前后端统一的前端工程化体系。",
}


def _find_domain(title):
    for keywords, spec in DOMAINS:
        if any(k in title for k in keywords):
            return spec
    return {
        "roles": ["管理员", "普通用户"],
        "extra_modules": [
            ("信息管理", "业务信息的录入、修改、删除与查询"),
            ("公告管理", "系统公告与通知的发布管理"),
        ],
        "extra_tables": [
            ("info", "业务信息表", "业务核心信息与状态字段"),
            ("notice", "公告信息表", "公告标题、内容与发布时间"),
        ],
    }


def build_system_design(title, techs, level="medium"):
    domain = _find_domain(title)
    modules = [{"name": n, "desc": d} for n, d in BASE_MODULES + domain["extra_modules"]]
    roles = domain["roles"]
    tables = [
        {"name": n, "title": t, "desc": d}
        for n, t, d in BASE_TABLES + domain["extra_tables"]
    ]
    features = [{"module": m["name"], "desc": m["desc"]} for m in modules]
    return {
        "modules": modules,
        "roles": roles,
        "tables": tables,
        "features": features,
        "domain_note": "根据题目关键词识别为:" + _domain_label(domain),
    }


def _domain_label(domain):
    names = [m[0] for m in domain["extra_modules"]]
    return "、".join(names[:3]) + " 等模块方向"


def _tech_main(techs):
    return techs[0] if techs else "主流 Web"


def _tech_texts(techs):
    texts = []
    for t in techs:
        texts.append(TECH_MAP.get(t, "「%s」是本次系统采用的关键技术之一,为系统的开发与稳定运行提供了基础能力。" % t))
    if not texts:
        texts.append(TECH_MAP["SpringBoot"])
    return texts


def _extra(level, pool):
    idx = {"small": 0, "medium": 1, "large": 2}.get(level, 1)
    return pool[idx]


def build_summary(title, techs, design, level):
    main_tech = _tech_main(techs)
    modules = "、".join(m["name"] for m in design["modules"][:4])
    extra = _extra(level, [
        "",
        "系统采用前后端分离的架构,后端负责业务逻辑与数据接口,前端负责页面展示与交互,整体结构清晰、易于维护。",
        "系统采用前后端分离的架构,后端负责业务逻辑与数据接口,前端负责页面展示与交互;在需求分析阶段明确了系统角色与核心业务流程,在设计阶段完成了总体架构、功能模块与数据库设计,并通过系统测试验证了主要功能的正确性。",
    ])
    summary = (
        "随着信息化建设的不断推进,传统的手工管理模式已难以满足日益增长的效率与规范化需求。"
        "本文设计并实现了一个基于%s 的%s,系统主要包含%s等核心功能模块,"
        "面向%s等角色提供服务。%s"
        "系统开发遵循软件工程流程,依次完成了需求分析、系统设计、系统实现与系统测试,"
        "测试结果表明系统各主要功能运行正常,能够满足日常业务需要,具有良好的实用性、稳定性与可扩展性。"
    ) % (main_tech, title, modules, "、".join(design["roles"]), extra)
    keywords = "、".join([m["name"] for m in design["modules"][:3]] + [design["roles"][-1]]) if design["modules"] else "系统"
    return "**摘要**:%s\n\n**关键词**:%s" % (summary, keywords)


def build_abstract(title, design):
    main_tech = _tech_main(["SpringBoot"])
    en = (
        "With the continuous development of information technology, traditional manual "
        "management methods can no longer meet the growing requirements of efficiency and "
        "standardization. This thesis designs and implements a web-based information "
        "management system built with %s technology. The system provides core functions "
        "such as user management, business information management, and system management, "
        "serving roles including administrator and ordinary users. Following the software "
        "engineering process, the system was developed through requirement analysis, system "
        "design, implementation, and testing. Test results show that the main functions "
        "operate correctly and the system meets the practical needs of daily business."
    ) % main_tech
    keywords = ", ".join(["information system", "management", "Web", "Spring Boot"])
    return "**Abstract**:%s\n\n**Keywords**:%s" % (en, keywords)


def build_ch1(title, techs, design, level):
    main_tech = _tech_main(techs)
    extra_bg = _extra(level, [
        "",
        "同时,互联网技术的普及使得用户对信息获取与业务办理的便捷性提出了更高要求。",
        "同时,互联网技术的普及使得用户对信息获取与业务办理的便捷性提出了更高要求,移动端与 Web 端的协同使用也已成为信息化系统的重要趋势,这对系统的稳定性、安全性与易用性提出了更高的标准。",
    ])
    extra_status = _extra(level, [
        "",
        "国内同类系统在功能覆盖上已经比较全面,但部分系统存在界面陈旧、操作繁琐、扩展性不足等问题。",
        "国外在信息化管理系统领域起步较早,形成了较为成熟的体系;国内同类系统在功能覆盖上已比较全面,但部分系统仍存在界面陈旧、操作繁琐、扩展性不足等问题,尤其是在业务适配与二次开发方面仍有提升空间。",
    ])
    return (
        "# 第 1 章 绪论\n\n"
        "## 1.1 研究背景与意义\n\n"
        "随着信息技术的快速发展,信息化管理已成为提高工作效率、规范业务流程的重要手段。"
        "针对%s,%s的研发具有明确的实际意义。%s"
        "通过本系统的建设,能够将分散的业务数据集中管理,减少人工操作带来的差错,"
        "提高信息查询与统计的效率,为管理者提供数据支撑,同时为使用者带来更便捷的服务体验。\n\n"
        "## 1.2 国内外研究现状\n\n"
        "在信息化管理系统领域,国内外均已开展了大量研究与实践。%s"
        "总体来看,基于 %s 技术栈开发前后端分离的 Web 系统,已成为当前主流的技术方案,"
        "其开发效率、维护性与用户体验均具有明显优势。\n\n"
        "## 1.3 主要研究内容\n\n"
        "本文的主要研究内容包括:\n\n"
        "- 系统需求分析:调研业务场景,明确系统角色、功能需求与非功能需求;\n"
        "- 系统设计:完成总体架构设计、功能模块设计与数据库设计;\n"
        "- 系统实现:基于%s技术栈完成各功能模块的开发;\n"
        "- 系统测试:设计测试用例,对系统功能进行验证并给出测试结论。\n\n"
        "## 1.4 论文组织结构\n\n"
        "本论文共分为七章:第 1 章为绪论,介绍研究背景与主要内容;第 2 章介绍相关技术;"
        "第 3 章进行系统需求分析;第 4 章进行系统设计;第 5 章介绍系统实现;"
        "第 6 章介绍系统测试;第 7 章对全文进行总结与展望。"
    ) % (title + "这一实际需求", "基于 " + main_tech + " 的" + title, extra_bg, extra_status, main_tech, ", ".join(techs[:2]))


def build_ch2(techs):
    parts = ["# 第 2 章 相关技术介绍\n\n本章对系统开发过程中采用的主要技术进行介绍,为后续章节的设计与实现奠定基础。\n"]
    for i, text in enumerate(_tech_texts(techs), start=1):
        name = techs[i - 1] if i - 1 < len(techs) else "相关技术"
        parts.append("## 2.%d %s\n\n%s" % (i, name, text))
    parts.append("\n综上,上述技术相互配合,能够满足系统在开发效率、运行性能与可维护性方面的要求。")
    return "\n".join(parts)


def build_ch3(title, design, level):
    extra = _extra(level, [
        "",
        "此外,系统还需要考虑数据备份、异常处理与并发访问等场景。",
        "此外,系统还需要考虑数据备份、异常处理、并发访问与权限隔离等场景,确保在多用户同时使用的情况下依然能够稳定运行。",
    ])
    modules = "\n".join("- %s:%s" % (m["name"], m["desc"]) for m in design["modules"])
    return (
        "# 第 3 章 系统需求分析\n\n"
        "## 3.1 可行性分析\n\n"
        "技术可行性:%s 等技术已经成熟稳定,社区资料丰富,团队具备相应的开发能力,技术风险较低。\n\n"
        "经济可行性:系统开发主要依靠开源技术与常规开发环境,成本可控;系统投入运行后能够显著提高业务处理效率,具有良好的投入产出比。\n\n"
        "操作可行性:系统界面简洁、操作流程清晰,用户经过简单培训即可上手使用,具备良好的操作可行性。\n\n"
        "## 3.2 功能需求分析\n\n"
        "通过对业务场景的分析,系统主要包含以下功能模块:\n\n%s\n\n"
        "【此处建议插入:图 3-1 系统用例图】(素材:角色与功能描述文字)\n\n"
        "## 3.3 非功能需求\n\n"
        "- 性能需求:系统应能支持一定规模的并发访问,主要操作响应时间在可接受范围内;\n"
        "- 安全需求:用户密码需加密存储,接口需进行权限校验,防止未授权访问;\n"
        "- 易用性需求:界面布局合理、操作提示清晰,保证用户能够快速上手;\n"
        "- 可维护性需求:代码遵循分层结构,模块之间低耦合,便于后续维护与扩展。%s"
    ) % ("相关开发技术", modules, extra)


def build_ch4(title, design, level):
    tables = "\n".join("- %s(%s):%s" % (t["name"], t["title"], t["desc"]) for t in design["tables"])
    modules = "\n".join("- %s:%s" % (m["name"], m["desc"]) for m in design["modules"])
    return (
        "# 第 4 章 系统设计\n\n"
        "## 4.1 总体架构设计\n\n"
        "系统采用前后端分离的分层架构:前端负责页面展示与用户交互,后端按照表现层、业务层与数据访问层进行划分,"
        "通过 RESTful 接口进行通信,数据库负责数据的持久化存储。整体架构层次清晰、职责明确,便于团队并行开发与后续维护。\n\n"
        "【此处建议插入:图 4-1 系统架构图】(素材:技术栈与部署说明文字)\n\n"
        "## 4.2 功能模块设计\n\n"
        "根据需求分析结果,系统划分为以下功能模块:\n\n%s\n\n"
        "【此处建议插入:图 4-2 功能模块图】(素材:模块说明文字,可自动预填)\n\n"
        "## 4.3 数据库设计\n\n"
        "数据库采用关系型数据库进行设计,主要数据表如下:\n\n%s\n\n"
        "各表之间通过外键建立关联,并针对常用查询字段建立索引,以保证数据一致性与查询性能。\n\n"
        "【此处建议插入:图 4-3 E-R 图】(素材:SQL 建表语句)\n\n"
        "## 4.4 接口设计\n\n"
        "系统后端提供统一风格的 RESTful 接口,使用 JSON 作为数据交换格式,主要接口包括登录认证、"
        "数据增删改查与统计查询等,接口按照功能模块进行分组,并统一返回状态码与提示信息,方便前端调用与异常处理。"
    ) % (modules, tables)


def build_ch5(title, design, level):
    first_modules = [m["name"] for m in design["modules"][:3]]
    impl = "\n".join(
        "- %s:实现%s相关功能,包括列表查询、条件筛选、新增编辑与删除操作,前端通过表单校验后调用后端接口,后端进行参数校验与权限判断后完成数据操作。" % (name, name)
        for name in first_modules
    )
    env_rows = "\n".join(
        "| %s | %s |" % (r[0], r[1])
        for r in [
            ("操作系统", "Windows / Linux"),
            ("后端环境", "JDK / Python 运行环境"),
            ("前端环境", "现代浏览器"),
            ("数据库", "MySQL"),
        ]
    )
    return (
        "# 第 5 章 系统实现\n\n"
        "## 5.1 开发环境\n\n"
        "系统的开发与运行环境如下:\n\n"
        "| 类别 | 说明 |\n|---|---|\n%s\n\n"
        "## 5.2 关键模块实现\n\n"
        "系统主要功能模块的实现情况如下:\n\n%s\n\n"
        "## 5.3 核心代码逻辑\n\n"
        "以核心业务处理为例,后端接口首先接收前端请求并完成参数校验,然后调用业务层方法处理业务规则,"
        "再通过数据访问层与数据库交互,最后将处理结果封装为统一格式返回给前端。核心流程可概括为:"
        "请求校验 → 业务处理 → 数据持久化 → 结果返回。\n\n"
        "```text\n处理流程:\n1. 前端提交请求参数\n2. 后端校验参数与权限\n3. 执行业务逻辑\n4. 读写数据库\n5. 返回统一响应\n```\n\n"
        "【此处建议插入:图 5-1 核心业务流程图】(素材:业务流程文字)"
    ) % (env_rows, impl)


def build_ch6(design, level):
    extra = _extra(level, [
        "",
        "测试过程覆盖了系统的主要功能模块与关键业务流程。",
        "测试过程覆盖了系统的主要功能模块与关键业务流程,并针对边界输入、异常操作与权限控制等场景补充了用例。",
    ])
    modules = [m["name"] for m in design["modules"][:4]]
    cases = "\n".join(
        "| TC-%02d | %s | 执行核心操作流程 | 操作成功且数据正确 | 通过 |" % (i + 1, name)
        for i, name in enumerate(modules)
    )
    return (
        "# 第 6 章 系统测试\n\n"
        "## 6.1 测试环境\n\n"
        "测试在本地开发环境完成,浏览器端与后端服务均正常运行,测试数据使用模拟数据。\n\n"
        "## 6.2 功能测试\n\n"
        "针对系统主要功能设计测试用例并执行,结果如下:\n\n"
        "| 用例编号 | 测试项 | 操作步骤 | 预期结果 | 实际结果 |\n|---|---|---|---|---|\n%s\n\n"
        "## 6.3 测试结论\n\n"
        "测试结果表明,系统各主要功能模块运行正常,功能实现与需求一致,"
        "界面交互流畅,数据存取正确,达到了预期的设计目标。%s"
    ) % (cases, extra)


def build_ch7(title, level):
    extra = _extra(level, [
        "",
        "后续还可以进一步优化界面交互、完善数据统计与分析功能。",
        "后续还可以进一步优化界面交互、完善数据统计与分析功能,并考虑引入更智能化的数据处理手段,提升系统的实用价值与竞争力。",
    ])
    return (
        "# 第 7 章 总结与展望\n\n"
        "## 7.1 工作总结\n\n"
        "本文完成了%s的需求分析、系统设计、系统实现与系统测试全过程,"
        "实现了主要功能模块,验证了系统的可行性与实用性。通过本项目的开发,"
        "加深了对软件工程流程的理解,也提升了实际开发与问题排查的能力。\n\n"
        "## 7.2 不足与展望\n\n"
        "系统目前仍存在一些不足,例如部分业务场景覆盖不够全面、并发性能有待进一步提升等。%s"
        "未来将在现有基础上持续完善,使系统更加成熟可靠。"
    ) % (title, extra)


def build_refs(techs):
    refs = [
        "李刚. 轻量级 Java EE 企业应用实战[M]. 北京:电子工业出版社, 2019.",
        "尤雨溪. Vue.js 设计与实现[M]. 北京:人民邮电出版社, 2021.",
        "唐汉明. 深入浅出 MySQL[M]. 北京:人民邮电出版社, 2018.",
        "张海藩. 软件工程导论[M]. 北京:清华大学出版社, 2020.",
    ]
    ref_lines = "\n".join("[%d] %s" % (i + 1, r) for i, r in enumerate(refs))
    return (
        "# 参考文献\n\n%s\n\n"
        "# 致谢\n\n"
        "本系统的设计与实现离不开老师与同学们的帮助与支持。感谢指导老师在项目过程中给予的悉心指导,"
        "感谢团队成员的通力合作,也感谢学校提供的学习与实践环境。由于本人水平有限,系统中难免存在不足之处,恳请各位老师批评指正。"
    ) % ref_lines


def chart_suggestions():
    return [
        {"fig": "图 3-1", "title": "系统用例图", "position": "第 3 章 需求分析", "material": "角色与功能描述文字"},
        {"fig": "图 4-1", "title": "系统架构图", "position": "第 4 章 系统设计", "material": "技术栈 / 部署说明文字"},
        {"fig": "图 4-2", "title": "功能模块图", "position": "第 4 章 模块设计", "material": "模块说明(可自动预填)"},
        {"fig": "图 4-3", "title": "E-R 图", "position": "第 4 章 数据库设计", "material": "SQL 建表语句"},
        {"fig": "图 5-1", "title": "核心业务流程图", "position": "第 5 章 系统实现", "material": "业务流程文字"},
    ]


def generate_paper(title, techs, level="medium", style="严谨学术"):
    design = build_system_design(title, techs, level)
    chapters = [
        {"seq": 0, "key": "summary", "title": "摘要与关键词", "content_md": build_summary(title, techs, design, level)},
        {"seq": 1, "key": "abstract", "title": "Abstract", "content_md": build_abstract(title, design)},
        {"seq": 2, "key": "ch1", "title": "第 1 章 绪论", "content_md": build_ch1(title, techs, design, level)},
        {"seq": 3, "key": "ch2", "title": "第 2 章 相关技术介绍", "content_md": build_ch2(techs)},
        {"seq": 4, "key": "ch3", "title": "第 3 章 系统需求分析", "content_md": build_ch3(title, design, level)},
        {"seq": 5, "key": "ch4", "title": "第 4 章 系统设计", "content_md": build_ch4(title, design, level)},
        {"seq": 6, "key": "ch5", "title": "第 5 章 系统实现", "content_md": build_ch5(title, design, level)},
        {"seq": 7, "key": "ch6", "title": "第 6 章 系统测试", "content_md": build_ch6(design, level)},
        {"seq": 8, "key": "ch7", "title": "第 7 章 总结与展望", "content_md": build_ch7(title, level)},
        {"seq": 9, "key": "refs", "title": "参考文献与致谢", "content_md": build_refs(techs)},
    ]
    full_md = "\n\n".join("# %s\n\n%s" % (c["title"], c["content_md"]) if c["seq"] > 1 else c["content_md"] for c in chapters)
    words = len(full_md.replace("\n", "").replace(" ", ""))
    return {
        "title": title,
        "techs": techs,
        "level": level,
        "style": style,
        "system_design": design,
        "chapters": chapters,
        "chart_suggestions": chart_suggestions(),
        "stats": {"word_count": words},
        "mode": "template",
    }


# ---------- 题目建议(本地模板) ----------

def _suggest_roles(keywords):
    kw = keywords or ""
    if any(k in kw for k in ("图书", "图书馆", "借阅", "书城")):
        return ["读者", "管理员"]
    if any(k in kw for k in ("医院", "门诊", "诊所", "患者", "挂号")):
        return ["患者", "医生", "管理员"]
    if any(k in kw for k in ("商城", "电商", "购物", "交易", "拍卖", "外卖", "订餐", "餐饮")):
        return ["普通用户", "商家", "管理员"]
    if any(k in kw for k in ("校园", "学生", "二手", "社团", "教务", "选课", "宿舍")):
        return ["学生", "教师", "管理员"]
    return ["普通用户", "管理员"]


def _suggest_suffix(keywords):
    kw = (keywords or "").strip()
    if any(kw.endswith(end) for end in ("系统", "平台", "网站", "小程序", "APP", "App")):
        return ""
    return "平台"


def suggest_topics(keywords, techs, count=4, batch=0):
    """根据研究方向关键词与技术栈生成 count 个可落地的题目建议。"""
    kw = (keywords or "").strip() or "智慧校园综合管理"
    techs = [t for t in (techs or []) if str(t).strip()] or ["SpringBoot", "Vue", "MySQL"]
    t1, t2, t3 = (techs + ["SpringBoot", "Vue", "MySQL"])[:3]
    roles = _suggest_roles(kw)
    r1, r2 = roles[0], roles[-1]
    suffix = _suggest_suffix(kw)
    domain = kw + suffix

    candidates = [
        {
            "title": "基于 %s 与 %s 的%s的设计与实现" % (t1, t2, domain),
            "techs": [t1, t2, t3],
            "description": "经典前后端分离方案,覆盖用户管理、%s等完整模块,实现难度适中、答辩稳妥,适合作为团队主推选题。" % domain,
            "tags": ["经典架构", "答辩稳妥"],
        },
        {
            "title": "面向%s的%s的设计与实现" % (r1, domain),
            "techs": [t1, t2],
            "description": "以%s为核心用户设计,贴近真实使用场景,功能针对性强,容易写出业务亮点。" % r1,
            "tags": ["用户导向", "业务聚焦"],
        },
        {
            "title": "%s的设计与实现——基于%s前后端分离架构" % (domain, t1),
            "techs": [t1, t2, t3],
            "description": "突出总体架构、接口设计与数据库设计,适合展示系统设计能力与工程规范。",
            "tags": ["架构优先", "工程规范"],
        },
        (
            {
                "title": "基于微信小程序与%s的%s" % (t1, domain),
                "techs": [t1, t2, "小程序"],
                "description": "结合移动端使用场景,体现多端协同与云服务能力,演示画面更丰富。",
                "tags": ["多端协同", "演示加分"],
            }
            if "小程序" in techs
            else {
                "title": "基于%s的%s的研发与实现" % (t1, domain),
                "techs": [t1, t3],
                "description": "围绕%s单栈展开,技术聚焦、代码量可控,适合小组内分工更细的情况。" % t1,
                "tags": ["技术聚焦", "轻量落地"],
            }
        ),
        {
            "title": "面向%s与%s的%s" % (r2, r1, domain),
            "techs": [t1, t2],
            "description": "双角色权限清晰,便于展示权限控制、流程审批与业务闭环,适合偏管理类系统。",
            "tags": ["权限设计", "流程闭环"],
        },
        {
            "title": "基于%s与%s的%s综合服务平台" % (t1, t3, kw),
            "techs": [t1, t2, t3],
            "description": "在核心业务之上叠加公告、统计等增值服务,功能面更全,适合需要展示系统完整度的小组。",
            "tags": ["功能完整", "系统性强"],
        },
    ]
    start = (batch * 2) % len(candidates)
    picked = (candidates * 2)[start:start + count]
    return picked
