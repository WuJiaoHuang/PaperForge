/* PaperForge 论文工坊 —— 前端逻辑 */

const TECH_PRESETS = [
  "SpringBoot", "Vue", "Vue3", "MySQL", "Redis", "MyBatis-Plus",
  "Python", "Django", "Flask", "小程序", "React", "Element Plus",
];
const DEFAULT_TECHS = ["SpringBoot", "Vue", "MySQL", "Redis"];
const HISTORY_KEY = "paperforge_v1_history";

const state = {
  payload: null,
  topics: [],
  batch: 0,
  selectedTopic: null,
  pollTimer: null,
  stageEls: [],
  renderedChapters: new Set(),
  designShown: false,
  chartExtras: [],
  chartImages: {},
};
const STAGE_NAMES = ["系统设定", "摘要", "Abstract", "绪论", "相关技术", "需求分析", "系统设计", "系统实现", "系统测试", "总结展望", "参考文献致谢"];
const CHART_POSITIONS = ["第 3 章 需求分析", "第 4 章 系统设计", "第 5 章 系统实现", "第 6 章 系统测试", "文末"];
let CHART_TYPES = [
  { type: "er", label: "E-R 图", hint: "粘贴 SQL 建表语句(CREATE TABLE …),留空则使用系统设定的数据表" },
  { type: "flow", label: "流程图", hint: "按顺序描述步骤,每行一步;留空则生成默认业务流程" },
  { type: "architecture", label: "系统架构图", hint: "每行一层(如:用户层:浏览器);留空则按技术栈生成" },
  { type: "module", label: "功能模块图", hint: "可留空,默认使用系统设定的功能模块" },
  { type: "usecase", label: "系统用例图", hint: "可留空,默认使用系统设定的角色与功能" },
  { type: "sequence", label: "时序图", hint: "每行格式:角色A -> 角色B: 消息;留空则生成默认交互时序" },
];
const $ = (id) => document.getElementById(id);

/* ---------- 技术栈 chips ---------- */
function initChips() {
  const wrap = $("techChips");
  wrap.innerHTML = "";
  TECH_PRESETS.forEach((t) => {
    const chip = document.createElement("span");
    chip.className = "chip" + (DEFAULT_TECHS.includes(t) ? " on" : "");
    chip.textContent = t;
    chip.dataset.tech = t;
    chip.onclick = () => chip.classList.toggle("on");
    wrap.appendChild(chip);
  });
}

function selectedTechs() {
  const list = [...document.querySelectorAll("#techChips .chip.on")].map((c) => c.dataset.tech);
  const custom = $("customTech").value.trim();
  if (custom && !list.includes(custom)) list.push(custom);
  return list;
}

$("addTech").onclick = () => {
  const v = $("customTech").value.trim();
  if (!v) return;
  const chip = document.createElement("span");
  chip.className = "chip on";
  chip.textContent = v;
  chip.dataset.tech = v;
  chip.onclick = () => chip.classList.toggle("on");
  $("techChips").appendChild(chip);
  $("customTech").value = "";
};
$("customTech").addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); $("addTech").click(); }
});

/* 关键词快捷提示 */
document.querySelectorAll(".hint-chip").forEach((btn) => {
  btn.onclick = () => { $("keywords").value = btn.dataset.kw; };
});

/* ---------- 题目建议 ---------- */
function setSuggestBusy(busy) {
  $("suggestBtn").disabled = busy;
  $("refreshBtn").disabled = busy;
}

async function suggestTopics() {
  const keywords = $("keywords").value.trim() || $("title").value.trim();
  const techs = selectedTechs();
  setSuggestBusy(true);
  $("topicHint").textContent = "正在生成备选题目…";
  try {
    const res = await fetch("/api/topics/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        keywords,
        techs,
        count: 4,
        batch: state.batch,
        use_ai: $("useAi").checked,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "生成题目失败");
    state.topics = data.topics || [];
    state.batch += 1;
    renderTopics(state.topics);
    $("refreshBtn").classList.remove("hidden");
    const noteEl = $("topicNote");
    if (data.note) { noteEl.textContent = data.note; noteEl.classList.remove("hidden"); }
    else { noteEl.classList.add("hidden"); }
    $("topicHint").textContent = "以下为系统推荐的备选题目,点击卡片选题;不满意可「重新生成」";
    return true;
  } catch (err) {
    $("topicHint").textContent = "生成失败:" + err.message;
    return false;
  } finally {
    setSuggestBusy(false);
  }
}

function renderTopics(topics) {
  const grid = $("topicGrid");
  grid.innerHTML = "";
  if (!topics.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = '<p class="empty-main">暂无备选题目</p><p class="field-tip">请点击「重新生成」</p>';
    grid.appendChild(empty);
    return;
  }
  topics.forEach((t, i) => {
    const card = document.createElement("article");
    card.className = "topic-card";
    if (state.selectedTopic && state.selectedTopic.title === t.title) card.classList.add("selected");
    const techs = (t.techs || []).map((x) => '<span class="topic-tech">' + escapeHtml(x) + "</span>").join("");
    const tags = (t.tags || []).map((x) => '<span class="topic-tag">' + escapeHtml(x) + "</span>").join("");
    card.innerHTML =
      '<span class="topic-badge">备选题目' + "一二三四五六".charAt(i) + "</span>" +
      "<h3>" + escapeHtml(t.title) + "</h3>" +
      '<div class="topic-techs">' + techs + "</div>" +
      '<p class="topic-desc">' + escapeHtml(t.description || "") + "</p>" +
      '<div class="topic-tags">' + tags + "</div>" +
      '<button class="btn-select" type="button">选择此题</button>';
    card.querySelector(".btn-select").onclick = () => selectTopic(t);
    grid.appendChild(card);
  });
  $("topicFooter").classList.remove("hidden");
  updateSelectedBar();
}

function selectTopic(topic) {
  state.selectedTopic = topic;
  $("title").value = topic.title;
  document.querySelectorAll(".topic-card").forEach((card) => {
    const h3 = card.querySelector("h3");
    card.classList.toggle("selected", h3 && h3.textContent === topic.title);
  });
  updateSelectedBar();
}

function clearTopic() {
  state.selectedTopic = null;
  $("title").value = "";
  document.querySelectorAll(".topic-card").forEach((c) => c.classList.remove("selected"));
  updateSelectedBar();
}

function updateSelectedBar() {
  const bar = $("selectedTopicBar");
  if (state.selectedTopic) {
    $("selectedTopicText").textContent = state.selectedTopic.title;
    bar.classList.remove("hidden");
  } else {
    bar.classList.add("hidden");
  }
}

$("suggestBtn").onclick = suggestTopics;
$("refreshBtn").onclick = suggestTopics;
$("clearTopicBtn").onclick = clearTopic;

/* ---------- 演示模式 ---------- */
$("demoBtn").onclick = async () => {
  $("title").value = "基于 SpringBoot 与 Vue 的校园二手交易平台";
  $("keywords").value = "校园二手交易";
  document.querySelectorAll("#techChips .chip").forEach((c) => {
    c.classList.toggle("on", ["SpringBoot", "Vue", "MySQL", "Redis"].includes(c.dataset.tech));
  });
  $("wordLevel").value = "medium";
  $("style").value = "严谨学术";
  const ok = await suggestTopics();
  if (!ok) return;
  if (state.topics.length) {
    selectTopic(state.topics[0]);
    generate();
  }
};

/* ---------- Markdown 渲染 ---------- */
function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inlineMd(s) {
  return escapeHtml(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function mdToHtml(md) {
  const lines = md.split("\n");
  let html = "";
  let listType = null;
  let inCode = false;
  let codeBuf = [];
  let tableBuf = [];

  const closeList = () => {
    if (listType) { html += listType === "ul" ? "</ul>" : "</ol>"; listType = null; }
  };
  const flushTable = () => {
    if (!tableBuf.length) return;
    const rows = tableBuf.map((r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));
    const header = rows[0];
    const body = rows.filter((r, i) => i > 0 && !/^[\s:\-|]+$/.test(rows[i].join("")));
    html += "<table><thead><tr>" + header.map((c) => "<th>" + inlineMd(c) + "</th>").join("") + "</tr></thead><tbody>";
    body.forEach((r) => { html += "<tr>" + r.map((c) => "<td>" + inlineMd(c) + "</td>").join("") + "</tr>"; });
    html += "</tbody></table>";
    tableBuf = [];
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const imgMatch = line.match(/^!\[(.*?)\]\((data:image\/png;base64,[^)]+)\)$/);
    if (imgMatch) {
      closeList();
      flushTable();
      html += '<figure class="paper-figure"><img src="' + imgMatch[2] + '" alt="' + escapeHtml(imgMatch[1]) +
        '"/><figcaption>' + escapeHtml(imgMatch[1]) + "</figcaption></figure>";
      continue;
    }
    if (line.startsWith("```")) {
      if (!inCode) { closeList(); flushTable(); inCode = true; codeBuf = []; }
      else {
        html += "<pre><code>" + escapeHtml(codeBuf.join("\n")) + "</code></pre>";
        inCode = false;
      }
      continue;
    }
    if (inCode) { codeBuf.push(line); continue; }
    if (line.startsWith("|")) { closeList(); tableBuf.push(line); continue; }
    flushTable();
    if (line.startsWith("### ")) { closeList(); html += "<h3>" + inlineMd(line.slice(4)) + "</h3>"; }
    else if (line.startsWith("## ")) { closeList(); html += "<h3>" + inlineMd(line.slice(3)) + "</h3>"; }
    else if (line.startsWith("# ")) { closeList(); html += "<h3>" + inlineMd(line.slice(2)) + "</h3>"; }
    else if (/^\s*[-*]\s+/.test(line)) {
      if (listType !== "ul") { closeList(); html += "<ul>"; listType = "ul"; }
      html += "<li>" + inlineMd(line.replace(/^\s*[-*]\s+/, "")) + "</li>";
    } else if (/^\s*\d+[.、]\s+/.test(line)) {
      if (listType !== "ol") { closeList(); html += "<ol>"; listType = "ol"; }
      html += "<li>" + inlineMd(line.replace(/^\s*\d+[.、]\s+/, "")) + "</li>";
    } else if (line.includes("【此处建议插入")) {
      closeList();
      html += '<div class="placeholder">' + inlineMd(line) + "</div>";
    } else if (line.startsWith(">")) {
      closeList();
      html += '<p class="note">' + inlineMd(line.replace(/^>\s?/, "")) + "</p>";
    } else if (line.trim()) {
      closeList();
      html += "<p>" + inlineMd(line) + "</p>";
    }
  }
  closeList();
  flushTable();
  if (inCode) html += "<pre><code>" + escapeHtml(codeBuf.join("\n")) + "</code></pre>";
  return html;
}

/* ---------- 生成(实时展示) ---------- */
async function generate() {
  const title = $("title").value.trim();
  if (!title) { alert("请先选择或填写论文题目"); $("title").focus(); return; }
  const body = {
    title,
    techs: selectedTechs(),
    word_level: $("wordLevel").value,
    style: $("style").value,
    use_ai: $("useAi").checked,
    requirements: $("requirements").value.trim(),
  };
  setBusy(true);
  showProgress();
  state.chartExtras = [];
  state.chartImages = {};
  $("progressText").textContent = "正在生成论文内容,已完成章节将实时显示…";
  $("progressFill").style.width = "2%";
  initStages();
  state.renderedChapters = new Set();
  state.designShown = false;
  try {
    const res = await fetch("/api/generate/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const start = await res.json();
    if (!res.ok) throw new Error(start.error || "启动生成失败");
    const jobId = start.job_id;
    clearInterval(state.pollTimer);
    state.pollTimer = setInterval(() => pollJob(jobId), 800);
  } catch (err) {
    $("progressText").textContent = "生成失败:" + err.message;
    setBusy(false);
  }
}
$("genBtn").onclick = generate;

async function pollJob(jobId) {
  try {
    const stRes = await fetch("/api/generate/partial/" + jobId);
    const st = await stRes.json();
    if (!stRes.ok) throw new Error(st.error || "获取进度失败");
    updateStages(st.current, st.total, st.stage);
    if (st.design && !state.designShown) {
      renderDesign(st.design);
      state.designShown = true;
    }
    const fresh = (st.chapters || []).filter((c) => !state.renderedChapters.has(c.seq));
    if (fresh.length) {
      appendChapters(fresh);
      fresh.forEach((c) => state.renderedChapters.add(c.seq));
    }
    if (st.status === "done") {
      clearInterval(state.pollTimer);
      const rRes = await fetch("/api/generate/result/" + jobId);
      const data = await rRes.json();
      if (!rRes.ok) throw new Error(data.error || "获取结果失败");
      state.payload = data;
      saveHistory(data);
      $("progressText").textContent = "生成完成";
      $("progressFill").style.width = "100%";
      setBusy(false);
      setTimeout(() => renderResult(data), 350);
    } else if (st.status === "error") {
      clearInterval(state.pollTimer);
      $("progressText").textContent = "生成失败:" + (st.error || "未知错误");
      setBusy(false);
    }
  } catch (err) {
    clearInterval(state.pollTimer);
    $("progressText").textContent = "生成失败:" + err.message;
    setBusy(false);
  }
}

function setBusy(busy) {
  $("genBtn").disabled = busy;
  $("demoBtn").disabled = busy;
  $("suggestBtn").disabled = busy;
  setExportEnabled(!busy);
}

function setExportEnabled(enabled) {
  $("exportWord").disabled = !enabled;
  $("exportMd").disabled = !enabled;
  $("copyBtn").disabled = !enabled;
}

function showProgress() {
  $("topicView").classList.add("hidden");
  $("progressWrap").classList.remove("hidden");
  $("resultWrap").classList.remove("hidden");
  $("designPanel").innerHTML = "";
  $("chapters").innerHTML = "";
  $("toc").innerHTML = "";
  $("chartPanel").classList.add("hidden");
  $("paperTitle").textContent = $("title").value.trim();
  $("paperMeta").textContent = "正在生成,内容实时更新…";
  setExportEnabled(false);
}

function initStages() {
  const wrap = $("stageList");
  wrap.innerHTML = "";
  state.stageEls = STAGE_NAMES.map((name) => {
    const el = document.createElement("span");
    el.className = "stage";
    el.textContent = name;
    wrap.appendChild(el);
    return el;
  });
}

function updateStages(current, total, stage) {
  const pct = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  $("progressFill").style.width = pct + "%";
  $("progressText").textContent =
    current > 0 ? "正在生成:" + stage + " (" + current + "/" + total + ")" : (stage || "准备中");
  state.stageEls.forEach((el, i) => {
    el.className = "stage" + (i < current ? " done" : i === current ? " active" : "");
  });
}

/* ---------- 结果渲染 ---------- */
function renderResult(payload) {
  $("progressWrap").classList.add("hidden");
  $("resultWrap").classList.remove("hidden");
  $("paperTitle").textContent = payload.title;
  const mode = payload.mode === "ai" ? "智能写作生成" : "本地模板生成";
  $("paperMeta").textContent =
    mode + " · 约 " + (payload.stats?.word_count || 0) + " 字 · " + (payload.generated_at || "");
  renderDesign(payload.system_design);
  renderChapters(payload.chapters);
  renderCharts(payload.chart_suggestions || []);
  if (payload.note) {
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = payload.note;
    $("resultWrap").appendChild(note);
  }
  setExportEnabled(true);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateWordCount() {
  if (!state.payload) return;
  const full = state.payload.chapters.map((x) => x.content_md || "").join("");
  const words = full.replace(/\n/g, "").replace(/ /g, "").length;
  state.payload.stats = state.payload.stats || {};
  state.payload.stats.word_count = words;
  const meta = $("paperMeta");
  if (meta) meta.textContent = meta.textContent.replace(/约 \d+ 字/, "约 " + words + " 字");
}

function renderDesign(design) {
  const wrap = $("designPanel");
  wrap.innerHTML = "<h3>系统设定(全篇一致的模块 / 角色 / 数据表)</h3>";
  const modules = design?.modules || [];
  const roles = design?.roles || [];
  const tables = design?.tables || [];
  wrap.innerHTML +=
    '<div class="design-row">' +
    modules.map((m) => '<span class="mini-chip"><b>' + m.name + "</b> " + m.desc + "</span>").join("") +
    "</div>";
  wrap.innerHTML +=
    '<div class="design-row">角色:' +
    roles.map((r) => '<span class="mini-chip">' + r + "</span>").join("") +
    '&nbsp;&nbsp;数据表:' +
    tables.map((t) => '<span class="mini-chip">' + t.name + "(" + t.title + ")</span>").join("") +
    "</div>";
}

function renderChapters(chapters) {
  $("chapters").innerHTML = "";
  $("toc").innerHTML = "";
  appendChapters(chapters);
}

function makeChapterCard(c) {
  const id = "chap-" + c.seq;
  const card = document.createElement("article");
  card.className = "chapter";
  card.id = id;
  const editable = !!state.payload;
  card.innerHTML =
    '<div class="chapter-card">' +
      '<div class="chapter-head"><h2>' + c.title + "</h2>" +
        '<div class="chapter-actions">' +
          '<button class="btn-mini btn-edit" type="button"' + (editable ? "" : " disabled") + ">编辑</button>" +
          '<button class="btn-mini btn-regen" type="button"' + (editable ? "" : " disabled") + ">重新生成</button>" +
        "</div></div>" +
      '<div class="chapter-body">' + mdToHtml(c.content_md) + "</div>" +
    "</div>";
  const link = document.createElement("a");
  link.href = "#" + id;
  link.textContent = c.title;
  link.onclick = (e) => { e.preventDefault(); card.scrollIntoView({ behavior: "smooth", block: "start" }); };
  if (editable) {
    card.querySelector(".btn-edit").onclick = () => enterEditMode(card, c);
    card.querySelector(".btn-regen").onclick = () => enterRegenMode(card, c);
  }
  return { card, link };
}

function renderChapterBody(card, md) {
  const body = card.querySelector(".chapter-body");
  body.innerHTML = mdToHtml(md);
}

function enterEditMode(card, c) {
  const body = card.querySelector(".chapter-body");
  const editBtn = card.querySelector(".btn-edit");
  const regenBtn = card.querySelector(".btn-regen");
  const ta = document.createElement("textarea");
  ta.className = "chapter-editor";
  ta.value = c.content_md;
  body.innerHTML = "";
  body.appendChild(ta);
  editBtn.textContent = "保存";
  regenBtn.textContent = "取消";
  editBtn.onclick = () => saveChapter(card, c, ta);
  regenBtn.onclick = () => exitEditMode(card, c);
  ta.focus();
}

function exitEditMode(card, c) {
  const editBtn = card.querySelector(".btn-edit");
  const regenBtn = card.querySelector(".btn-regen");
  renderChapterBody(card, c.content_md);
  editBtn.textContent = "编辑";
  regenBtn.textContent = "重新生成";
  editBtn.onclick = () => enterEditMode(card, c);
  regenBtn.onclick = () => enterRegenMode(card, c);
}

function saveChapter(card, c, ta) {
  if (!state.payload) return;
  const idx = state.payload.chapters.findIndex((x) => x.seq === c.seq);
  if (idx === -1) return;
  state.payload.chapters[idx].content_md = ta.value;
  c.content_md = ta.value;
  updateWordCount();
  saveHistory(state.payload);
  exitEditMode(card, c);
}

function enterRegenMode(card, c) {
  if (!state.payload) return;
  const body = card.querySelector(".chapter-body");
  const editBtn = card.querySelector(".btn-edit");
  const regenBtn = card.querySelector(".btn-regen");
  const box = document.createElement("div");
  box.className = "regen-box";
  const ta = document.createElement("textarea");
  ta.className = "regen-input";
  ta.placeholder = "输入修改意见(可选),例如:精简篇幅、补充数据库设计细节、语气更正式;留空则直接重新生成";
  box.appendChild(ta);
  body.before(box);
  editBtn.textContent = "确认生成";
  regenBtn.textContent = "取消";
  editBtn.onclick = () => doRegenerate(card, c, ta, box, editBtn, regenBtn);
  regenBtn.onclick = () => exitRegenMode(card, c, box);
  ta.focus();
}

function exitRegenMode(card, c, box) {
  if (box) box.remove();
  const editBtn = card.querySelector(".btn-edit");
  const regenBtn = card.querySelector(".btn-regen");
  editBtn.textContent = "编辑";
  regenBtn.textContent = "重新生成";
  editBtn.onclick = () => enterEditMode(card, c);
  regenBtn.onclick = () => enterRegenMode(card, c);
}

async function doRegenerate(card, c, ta, box, editBtn, regenBtn) {
  if (!state.payload) return;
  const instructions = ta.value.trim();
  editBtn.disabled = true;
  regenBtn.disabled = true;
  editBtn.textContent = "生成中…";
  try {
    const res = await fetch("/api/generate/chapter", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: state.payload.title,
        techs: state.payload.techs || [],
        word_level: state.payload.level || "medium",
        style: state.payload.style || "严谨学术",
        use_ai: $("useAi").checked,
        chapter_key: c.key,
        chapter_title: c.title,
        hint: c.hint || "",
        instructions,
        requirements: state.payload.requirements || "",
        system_design: state.payload.system_design || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "重新生成失败");
    const idx = state.payload.chapters.findIndex((x) => x.seq === c.seq);
    if (idx !== -1) {
      state.payload.chapters[idx].content_md = data.content_md;
      c.content_md = data.content_md;
      renderChapterBody(card, data.content_md);
      updateWordCount();
      saveHistory(state.payload);
    }
    if (data.note) alert(data.note);
  } catch (err) {
    alert(err.message);
  } finally {
    exitRegenMode(card, c, box);
    editBtn.disabled = false;
    regenBtn.disabled = false;
  }
}

function appendChapters(chapters) {
  const wrap = $("chapters");
  const toc = $("toc");
  chapters.forEach((c) => {
    const { card, link } = makeChapterCard(c);
    wrap.appendChild(card);
    toc.appendChild(link);
  });
}

function renderCharts(suggestions) {
  const wrap = $("chartPanel");
  const all = (suggestions || []).concat(state.chartExtras || []);
  if (!all.length) { wrap.classList.add("hidden"); return; }
  wrap.classList.remove("hidden");
  wrap.innerHTML =
    '<div class="chart-panel-head"><h3>生图清单(填写素材后点击「生成图表」)</h3>' +
    '<div class="chart-add"><select id="chartTypeSelect">' +
    CHART_TYPES.map((t) => '<option value="' + t.type + '">' + escapeHtml(t.label) + "</option>").join("") +
    '</select><select id="chartPosSelect">' +
    CHART_POSITIONS.map((p) => "<option>" + p + "</option>").join("") +
    '</select><button id="addChartBtn" class="btn-mini" type="button">添加图表</button></div></div>';
  all.forEach((s) => {
    const item = document.createElement("div");
    item.className = "chart-item";
    const hint = chartHint(inferChartType(s)) || s.material || "";
    const canDelete = state.chartExtras.includes(s);
    item.innerHTML =
      '<div class="chart-item-head"><span class="chart-fig">' + escapeHtml(s.fig || "新增") + "</span>" +
      "<b>" + escapeHtml(s.title || "") + '</b><span class="chart-pos">' + escapeHtml(s.position || "自定义图表") + "</span></div>" +
      '<textarea class="chart-material" rows="2" placeholder="' + escapeHtml(hint) + '"></textarea>' +
      '<div class="chart-item-actions">' +
      '<button class="btn-mini btn-gen-chart" type="button">生成图表</button>' +
      (canDelete ? '<button class="btn-mini btn-del-chart" type="button">删除</button>' : "") +
      "</div>" +
      '<div class="chart-result"></div>';
    item.querySelector(".chart-material").value = defaultChartPrompt(s);
    item.querySelector(".btn-gen-chart").onclick = () =>
      generateChart(item.querySelector(".chart-material"), item.querySelector(".chart-result"), s);
    if (canDelete) {
      item.querySelector(".btn-del-chart").onclick = () => {
        state.chartExtras = state.chartExtras.filter((x) => x !== s);
        renderCharts(state.payload ? state.payload.chart_suggestions : []);
      };
    }
    wrap.appendChild(item);
  });
  $("addChartBtn").onclick = addChartItem;
}

function inferChartType(s) {
  if (s && s.type) return s.type;
  const t = ((s && s.title) || "") + ((s && s.material) || "");
  if (t.includes("架构")) return "architecture";
  if (t.includes("用例")) return "usecase";
  if (t.includes("E-R") || t.includes("ER") || t.includes("实体")) return "er";
  if (t.includes("流程")) return "flow";
  if (t.includes("时序")) return "sequence";
  if (t.includes("模块")) return "module";
  return "module";
}

function chartHint(type) {
  const t = CHART_TYPES.find((x) => x.type === type);
  return t ? t.hint : "";
}

function addChartItem() {
  const t = CHART_TYPES.find((x) => x.type === $("chartTypeSelect").value) || CHART_TYPES[0];
  const pos = $("chartPosSelect") ? $("chartPosSelect").value : "第 4 章 系统设计";
  state.chartExtras = state.chartExtras || [];
  state.chartExtras.push({ fig: "新增", title: t.label, type: t.type, position: pos, material: t.hint });
  renderCharts(state.payload ? state.payload.chart_suggestions : []);
}

function defaultChartPrompt(s) {
  if (s && s.prompt) return s.prompt;
  const p = state.payload;
  const title = p ? p.title : "";
  const techs = p && p.techs && p.techs.length ? p.techs.join("、") : "";
  const design = p ? p.system_design : null;
  const tables = design && design.tables ? design.tables.map((t) => (t.name || "") + "(" + (t.title || "") + ")").join("、") : "";
  const modules = design && design.modules ? design.modules.map((m) => m.name).join("、") : "";
  const roles = design && design.roles ? design.roles.join("、") : "";
  const features = design && design.features
    ? design.features.map((f) => (typeof f === "string" ? f : f.desc)).join("、")
    : "";
  const flowSteps = design && design.features && design.features.length
    ? design.features.slice(0, 3)
      .map((f) => (typeof f === "string" ? f : (f.desc || f.module || "")).slice(0, 14))
      .join("\n")
    : "用户发起请求\n系统校验与业务处理\n读写数据库";
  const type = inferChartType(s);
  switch (type) {
    case "er":
      return "请根据以下系统数据表绘制 E-R 图。\n论文题目:" + title + "\n数据表:" + (tables || "系统数据表") +
        "\n(可粘贴 SQL 建表语句替换,系统将解析生成实体与关系)";
    case "flow":
      return "请根据以下业务流程绘制流程图。\n论文题目:" + title + "\n用户登录系统\n" + flowSteps + "\n数据保存与结果返回";
    case "architecture":
      return "请根据以下技术栈绘制系统架构图。\n技术栈:" + (techs || "系统技术栈") +
        "\n层次:用户层 → 前端展示层 → 业务逻辑层 → 数据存储层";
    case "module":
      return "请根据系统功能模块绘制功能模块图。\n论文题目:" + title + "\n模块清单:" + (modules || "用户管理、业务管理、系统管理");
    case "usecase":
      return "请根据系统角色与功能绘制用例图。\n论文题目:" + title + "\n角色:" + (roles || "管理员、普通用户") +
        "\n功能:" + (features || "登录、业务管理、数据查询");
    case "sequence":
      return "请根据系统交互流程绘制时序图。\n论文题目:" + title +
        "\n用户 -> 系统: 提交请求\n系统 -> 数据库: 读写数据\n系统 -> 用户: 返回结果";
    default:
      return "请根据论文《" + title + "》绘制所需图表,可按需要修改下方指令。";
  }
}

async function generateChart(textarea, resultEl, s) {
  const material = textarea.value.trim();
  resultEl.innerHTML = '<span class="chart-loading">正在绘制…</span>';
  try {
    const res = await fetch("/api/charts/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chart_type: inferChartType(s),
        title: s.title,
        material,
        techs: state.payload ? state.payload.techs || [] : [],
        use_ai: $("useAi").checked,
        system_design: state.payload ? state.payload.system_design : null,
      }),
    });
    if (!res.ok) {
      let msg = "生成失败";
      try { const d = await res.json(); msg = d.error || msg; } catch { /* ignore */ }
      throw new Error(msg);
    }
    const blob = await res.blob();
    const b64 = await blobToBase64(blob);
    const key = (s.fig || "chart") + "|" + (s.title || "");
    state.chartImages = state.chartImages || {};
    state.chartImages[key] = b64;
    resultEl.innerHTML =
      '<img class="chart-img" src="data:image/png;base64,' + b64 + '" alt="' + escapeHtml(s.title || "") + '" />' +
      '<div class="chart-download">' +
      '<a class="btn-mini" href="data:image/png;base64,' + b64 + '" download="' +
      escapeHtml((s.fig || "chart") + "_" + (s.title || "")) + '.png">下载图片</a>' +
      '<button class="btn-mini btn-place-chart" type="button">放入论文指定位置</button>' +
      "</div>";
    resultEl.querySelector(".btn-place-chart").onclick = () => placeChartInPaper(s, b64);
  } catch (err) {
    resultEl.innerHTML = '<span class="chart-error">' + escapeHtml(err.message) + "</span>";
  }
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function placeChartInPaper(s, b64) {
  if (!state.payload) return;
  const imgLine = "![" + (s.fig || "图") + " " + (s.title || "") + "](data:image/png;base64," + b64 + ")";
  const figMatch = (s.fig || "").match(/图\s*\d+\s*[-－]\s*\d+/);
  const figNum = figMatch ? figMatch[0].replace(/\s+/g, " ").replace("－", "-") : "";
  let placed = false;
  state.payload.chapters.forEach((ch) => {
    if (placed) return;
    const lines = ch.content_md.split("\n");
    const out = [];
    for (const line of lines) {
      if (!placed && figNum && line.includes(figNum) && line.includes("此处建议插入")) {
        out.push(imgLine);
        placed = true;
      } else {
        out.push(line);
      }
    }
    ch.content_md = out.join("\n");
  });
  if (!placed) {
    const pos = s.position || "";
    const m = pos.match(/第\s*(\d)\s*章/);
    let target = null;
    if (m) target = state.payload.chapters.find((x) => x.key === "ch" + m[1]);
    if (!target && pos.includes("文末")) target = state.payload.chapters[state.payload.chapters.length - 1];
    if (!target) target = state.payload.chapters[state.payload.chapters.length - 1];
    target.content_md = (target.content_md.trimEnd() + "\n\n" + imgLine).trim();
  }
  renderChapters(state.payload.chapters);
  saveHistory(state.payload);
  updateWordCount();
  alert("图片已放入论文" + (figNum ? "对应占位处" : "指定章节"));
}

async function loadChartTypes() {
  try {
    const res = await fetch("/api/charts/types");
    const data = await res.json();
    if (data.types && data.types.length) CHART_TYPES = data.types;
  } catch { /* 使用内置默认 */ }
}

/* ---------- 导出 ---------- */
async function exportFile(path) {
  if (!state.payload) return;
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payload: state.payload }),
    });
    if (!res.ok) throw new Error("导出失败");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = path.includes("docx") ? "论文工坊_论文初稿.docx" : "论文工坊_论文初稿.md";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert(err.message);
  }
}
$("exportWord").onclick = () => exportFile("/api/export/docx");
$("exportMd").onclick = () => exportFile("/api/export/md");

$("copyBtn").onclick = async () => {
  if (!state.payload) return;
  const md = state.payload.chapters
    .map((c) => c.seq > 1 ? "# " + c.title + "\n\n" + c.content_md : c.content_md)
    .join("\n\n")
    .replace(/!\[([^\]]*)\]\(data:image\/png;base64,[^)]+\)/g, "【已插入图表:$1】");
  try { await navigator.clipboard.writeText(md); alert("全文已复制"); }
  catch { alert("复制失败,请手动复制"); }
};

/* ---------- 历史 ---------- */
function saveHistory(payload) {
  const list = loadHistory();
  list.unshift({ ts: Date.now(), title: payload.title, payload });
  while (list.length > 5) list.pop();
  localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
  renderHistory();
}

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); }
  catch { return []; }
}

function renderHistory() {
  const list = loadHistory();
  $("historyWrap").classList.toggle("hidden", list.length === 0);
  const ul = $("historyList");
  ul.innerHTML = "";
  list.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = new Date(item.ts).toLocaleString() + " · " + item.title;
    li.onclick = () => {
      state.payload = item.payload;
      renderResult(item.payload);
      window.scrollTo({ top: 0, behavior: "smooth" });
    };
    ul.appendChild(li);
  });
}

/* ---------- AI 可用性 ---------- */
async function checkAi() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.ai_available) {
      $("useAi").disabled = false;
      $("useAi").checked = true;
      $("statusText").textContent = "系统服务正常 · 智能写作已启用";
    }
  } catch { /* 保持默认 */ }
}

/* 顶栏固定:自动量取高度,给页面留白并同步锚点偏移 */
function syncTopbar() {
  const top = document.querySelector(".sticky-top");
  if (!top) return;
  const h = top.offsetHeight + "px";
  document.documentElement.style.setProperty("--topbar-h", h);
  document.body.style.paddingTop = h;
}
window.addEventListener("load", syncTopbar);
window.addEventListener("resize", syncTopbar);

initChips();
renderHistory();
checkAi();
syncTopbar();
loadChartTypes();
