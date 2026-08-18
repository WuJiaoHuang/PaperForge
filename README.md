# 论文工坊 PaperForge

一个本地运行的全栈 Demo:输入研究方向与技术栈,系统推荐 4 个毕业设计题目(支持「换一批」),选定后一键生成结构完整的论文初稿(中文/英文摘要、七章正文、参考文献致谢),支持章节预览、图表建议清单、Word / Markdown 导出与本地历史。

## 功能亮点

- 🎯 智能选题:输入关键词与技术栈,一次给出 4 个可落地题目,不满意可「换一批」
- ✍️ 论文自动生成:配置 DeepSeek API Key 后由 AI 逐章撰写;未配置时自动降级为本地模板,演示不中断
- 🎨 现代化界面:卡片式选题、章节级生成进度、一键导出 Word / Markdown

## 快速启动

1. 安装依赖(仅首次):双击 `install_deps.bat`(依赖安装到本目录 `deps`,不污染系统环境)
2. 启动:双击 `run.bat`,浏览器自动打开 `http://127.0.0.1:8000`
3. 点击「✨ 演示模式」一键体验;或填写研究方向 →「🎯 生成题目建议」→ 选题 →「开始生成论文」

## 启用真实 AI(DeepSeek)

1. 复制 `.env.example` 为 `.env`,填写 `DEEPSEEK_API_KEY`
2. 重启服务,右上角出现「DeepSeek AI 已连接」开关(默认开启)
3. 未配置或调用失败时,系统自动降级为本地模板模式

> ⚠️ `.env` 已被 `.gitignore` 忽略,严禁把真实密钥提交到仓库。

## 目录结构

```
paperforge/
├── run.bat / install_deps.bat
├── requirements.txt / .env.example / .gitignore
├── backend/
│   ├── main.py            # FastAPI 入口:选题建议、论文生成、导出接口
│   ├── template_engine.py # 本地模板引擎(选题建议 + 无 Key 兜底生成)
│   ├── ai_client.py       # DeepSeek 接入(选题、逐章写作,失败自动降级)
│   └── exporter.py        # Word / Markdown 导出
└── frontend/              # 单页前端(原生 HTML/CSS/JS)
```

## 多人协作

- 代码仓库:Gitee `PaperForgeTeam/PaperForge`(私有组织仓库,成员可见)
- 协作规范(分支命名、提交格式、Pull Request 流程)见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 说明

- 生成的论文与图表均为 AI 辅助初稿,仅供写作参考,需人工核实后使用
- 图表机制:系统只给出图表建议清单与正文占位,不画图;后续版本由用户上传素材后系统绘制
