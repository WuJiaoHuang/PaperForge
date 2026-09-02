# 论文工坊 PaperForge

毕业设计论文写作辅助系统。基于研究方向与所选技术栈，推荐备选题目，自动生成结构完整的论文初稿，并提供图表生成与文档导出能力。

## 已实现功能

### 1. 选题

- 用户可直接输入论文题目，也可点击「一键推荐」获取 4 个备选题目，不满意可重新生成
- 推荐结果结合研究方向关键词与所选技术栈，支持自定义技术栈

### 2. 论文生成

- 支持智能写作（DeepSeek），未配置密钥时自动使用本地模板，演示不中断
- 生成前可填写补充需求，论文按需求撰写；不填也可正常生成
- 生成任务由 Celery 异步执行，生成过程通过 SSE 展示；当前 SSE 采用数据库轮询论文状态，Redis Pub/Sub 尚未实现

### 3. 章节编辑与单章重写

- 每个章节可单独编辑（Markdown 原文），保存后立即生效
- 每个章节可单独重新生成；重新生成前可填写修改意见，写作引擎按意见调整
- 编辑或重写后字数统计与本地历史自动更新

### 4. 图表生成（生图清单）

- 内置 6 种图表类型：E-R 图、流程图、系统架构图、功能模块图、系统用例图、时序图
- 每项图表带有基于论文内容的默认素材说明，可自行修改
- 生成方式：写作引擎将素材转换为标准 PlantUML 代码，本地渲染为 PNG；渲染失败自动降级
- 支持添加自定义图表并指定放置章节，生成后可一键放入论文对应位置
- 导出 Word 时图表自动嵌入论文对应位置

### 5. 导出与历史

- 支持导出 Word 文档与 Markdown 文件，支持复制全文
- 本地保存最近 5 次生成记录，可随时重新打开

## 环境要求

- Python 3.10 及以上
- MySQL 8.x（业务数据存储，后端使用 SQLAlchemy / aiomysql 访问）
- Redis（Celery broker/result backend；当前不承担 SSE Pub/Sub）
- Java 17 及以上（用于 PlantUML 渲染）
- Graphviz（PlantUML 依赖，用于部分图型的自动布局）
- Node.js 18 及以上（构建 Vue 前端）

## 快速启动

1. 安装依赖：双击 `install_deps.bat`（使用当前激活的 Python 环境执行 `python -m pip install -r requirements.txt`，PlantUML 渲染器下载到 `tools/plantuml.jar`，Vue 前端自动构建）
2. 启动：双击 `run.bat`，浏览器自动打开 `http://127.0.0.1:8000`
3. 使用「演示模式」或按流程操作：填写论文题目 → 一键推荐 → 选择题目 → 开始生成论文

前端为 Vue 3 + Vite 工程，源码位于 `frontend/src`，构建产物输出到 `frontend/dist`。如需手动构建：

```
cd frontend
npm install
npm run build
```

## 后端架构说明

- Web 框架：FastAPI
- 数据库：MySQL，ORM 使用 SQLAlchemy，异步驱动使用 aiomysql
- 异步任务：Celery
- Redis：用于 Celery broker/result backend
- 生成进度：SSE 端点当前采用数据库轮询论文状态；Redis Pub/Sub 尚未接入

## 配置智能写作（DeepSeek）

1. 复制 `.env.example` 为 `.env`，填写 `DEEPSEEK_API_KEY`
2. 重启服务，页面出现「智能写作模式」开关（默认开启）
3. 未配置或调用失败时自动使用本地模板，功能不中断

注意：`.env` 已被 `.gitignore` 忽略，严禁提交密钥。

## 目录结构

```
paperforge/
├── run.bat / install_deps.bat
├── requirements.txt / .env.example / .gitignore
├── backend/
│   ├── main.py            # FastAPI 入口
│   ├── core/              # AI、模板、图表等核心能力
│   ├── tasks/             # Celery 异步任务
│   └── writing/           # 论文、章节、设计版本、导出等 V2 模块
└── frontend/              # Vue 3 + Vite 前端工程
    ├── index.html         # 页面入口
    ├── src/App.vue        # 主组件
    ├── src/components/    # 章节卡片、图表项等组件
    ├── src/store.js       # 全局状态
    ├── src/api.js         # 接口封装
    ├── src/utils.js       # 渲染与工具函数
    └── dist/              # 构建产物（git 忽略）
```

## 团队协作

- 代码仓库：Gitee `PaperForgeTeam/PaperForge`（私有组织仓库，成员可见）
- 协作规范（分支命名、提交格式、Pull Request 流程）见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 说明

- 生成的论文初稿仅供参考，需人工核实后使用
- 论文中的图表由素材生成，素材不足时基于系统设定自动补全
