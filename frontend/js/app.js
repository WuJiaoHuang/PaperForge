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
};
const STAGE_NAMES = ["系统设定", "摘要", "Abstract", "绪论", "相关技术", "需求分析", "系统设计", "系统实现", "系统测试", "总结展望", "参考文献致谢"];
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
  const keywords = $("keywords").value.trim();
  if (!keywords) { alert("请先填写研究方向关键词"); $("keywords").focus(); return false; }
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
  };
  setBusy(true);
  showProgress();
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
  card.innerHTML = '<div class="chapter-card"><h2>' + c.title + "</h2>" + mdToHtml(c.content_md) + "</div>";
  const link = document.createElement("a");
  link.href = "#" + id;
  link.textContent = c.title;
  link.onclick = (e) => { e.preventDefault(); card.scrollIntoView({ behavior: "smooth", block: "start" }); };
  return { card, link };
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
  if (!suggestions.length) { wrap.classList.add("hidden"); return; }
  wrap.classList.remove("hidden");
  wrap.innerHTML =
    "<h3>图表建议清单(系统不画图,你上传素材后系统绘制)</h3>" +
    "<table><thead><tr><th>图号</th><th>图题</th><th>建议位置</th><th>所需素材</th></tr></thead><tbody>" +
    suggestions.map((s) =>
      "<tr><td>" + s.fig + "</td><td>" + s.title + "</td><td>" + s.position +
      '</td><td class="material">' + s.material + "</td></tr>"
    ).join("") +
    "</tbody></table>";
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
  const md = state.payload.chapters.map((c) => c.seq > 1 ? "# " + c.title + "\n\n" + c.content_md : c.content_md).join("\n\n");
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

initChips();
renderHistory();
checkAi();
