<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api } from './api'
import { CHART_POSITIONS, DEFAULT_TECHS, STAGE_NAMES, TECH_PRESETS, store } from './store'
import { downloadBlob, loadHistory, mdToHtml, saveHistory } from './utils'
import ChapterCard from './components/ChapterCard.vue'
import ChartItem from './components/ChartItem.vue'

const customTech = ref('')
const chartTypeSel = ref('er')
const chartPosSel = ref('第 4 章 系统设计')
const designShown = ref(false)

const selectedTechs = computed(() => store.techs)
function isTechOn(t) { return store.techs.includes(t) }
function toggleTech(t) {
  const i = store.techs.indexOf(t)
  if (i >= 0) store.techs.splice(i, 1)
  else store.techs.push(t)
}
function addCustomTech() {
  const v = customTech.value.trim()
  if (!v) return
  if (!store.customTechs.includes(v)) store.customTechs.push(v)
  if (!store.techs.includes(v)) store.techs.push(v)
  customTech.value = ''
}
function onCustomKey(e) { if (e.key === 'Enter') { e.preventDefault(); addCustomTech() } }

const topicHint = computed(() => store.topicHint)

async function suggestTopics() {
  const keywords = store.keywords.trim() || store.title.trim()
  store.topicHint = '正在生成备选题目…'
  store.busy = true
  try {
    const res = await api.suggest({
      keywords,
      techs: store.techs,
      count: 4,
      batch: store.batch,
      use_ai: store.useAi,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || '生成题目失败')
    store.topics = data.topics || []
    store.batch += 1
    store.refreshVisible = true
    store.topicNote = data.note || ''
    store.topicHint = '以下为系统推荐的备选题目,点击卡片选题;不满意可「重新生成」'
    return true
  } catch (err) {
    store.topicHint = '生成失败:' + err.message
    return false
  } finally {
    store.busy = false
  }
}

function selectTopic(t) {
  store.selectedTopic = t
  store.title = t.title
}
function clearTopic() {
  store.selectedTopic = null
  store.title = ''
}

async function demo() {
  store.title = '基于 SpringBoot 与 Vue 的校园二手交易平台'
  store.keywords = '校园二手交易'
  store.techs = [...DEFAULT_TECHS]
  store.wordLevel = 'medium'
  store.style = '严谨学术'
  const ok = await suggestTopics()
  if (!ok) return
  if (store.topics.length) {
    selectTopic(store.topics[0])
    generate()
  }
}

async function generate() {
  const title = store.title.trim()
  if (!title) { alert('请先选择或填写论文题目'); return }
  const body = {
    title,
    techs: store.techs,
    word_level: store.wordLevel,
    style: store.style,
    use_ai: store.useAi,
    requirements: store.requirements.trim(),
  }
  store.busy = true
  store.view = 'progress'
  store.chartExtras = []
  store.chartImages = {}
  store.liveDesign = null
  store.liveChapters = []
  store.renderedSeq = []
  designShown.value = false
  store.current = 0
  store.total = 11
  store.stageText = '正在生成论文内容,已完成章节将实时显示…'
  store.progressPct = 2
  try {
    const res = await api.generateStart(body)
    const start = await res.json()
    if (!res.ok) throw new Error(start.error || '启动生成失败')
    const jobId = start.job_id
    clearInterval(store.pollTimer)
    store.pollTimer = setInterval(() => pollJob(jobId), 800)
  } catch (err) {
    store.stageText = '生成失败:' + err.message
    store.busy = false
  }
}

async function pollJob(jobId) {
  try {
    const st = await api.generatePartial(jobId)
    if (st.error) throw new Error(st.error)
    store.current = st.current || 0
    store.total = st.total || 11
    store.progressPct = st.total > 0 ? Math.min(100, Math.round((st.current / st.total) * 100)) : 0
    store.stageText = st.current > 0 ? '正在生成:' + st.stage + ' (' + st.current + '/' + st.total + ')' : (st.stage || '准备中')
    if (st.design && !designShown.value) {
      store.liveDesign = st.design
      designShown.value = true
    }
    const fresh = (st.chapters || []).filter((c) => !store.renderedSeq.includes(c.seq))
    if (fresh.length) {
      store.liveChapters = store.liveChapters.concat(fresh)
      fresh.forEach((c) => store.renderedSeq.push(c.seq))
    }
    if (st.status === 'done') {
      clearInterval(store.pollTimer)
      const data = await api.generateResult(jobId)
      store.payload = data
      saveHistory(data)
      store.stageText = '生成完成'
      store.progressPct = 100
      store.busy = false
      setTimeout(() => {
        store.view = 'result'
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }, 350)
    } else if (st.status === 'error') {
      clearInterval(store.pollTimer)
      store.stageText = '生成失败:' + (st.error || '未知错误')
      store.busy = false
    }
  } catch (err) {
    clearInterval(store.pollTimer)
    store.stageText = '生成失败:' + err.message
    store.busy = false
  }
}

const resultChapters = computed(() => (store.payload ? store.payload.chapters || [] : []))
const wordCount = computed(() => {
  if (!store.payload) return 0
  return store.payload.chapters
    .map((x) => x.content_md || '')
    .join('')
    .replace(/\n/g, '')
    .replace(/ /g, '').length
})
const paperMeta = computed(() => {
  if (!store.payload) return ''
  const mode = store.payload.mode === 'ai' ? '智能写作生成' : '本地模板生成'
  return mode + ' · 约 ' + wordCount.value + ' 字 · ' + (store.payload.generated_at || '')
})
const designModules = computed(() => (store.liveDesign || (store.payload && store.payload.system_design) || {}))
const chartList = computed(() => {
  store.chartVersion // 触发响应
  const base = store.payload ? store.payload.chart_suggestions || [] : []
  return base.concat(store.chartExtras)
})

function addChartItem() {
  const t = store.chartTypes.find((x) => x.type === chartTypeSel.value) || store.chartTypes[0]
  store.chartExtras.push({ fig: '新增', title: t.label, type: t.type, position: chartPosSel.value, material: t.hint })
  store.chartVersion += 1
}
function deleteChartItem(item) {
  store.chartExtras = store.chartExtras.filter((x) => x !== item)
  store.chartVersion += 1
}
function chartChanged() { /* 章节/字数变化由 computed 自动更新 */ }

function scrollToChapter(seq) {
  const el = document.getElementById('chap-' + seq)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function exportDocx() {
  if (!store.payload) return
  try { await downloadBlob(await api.exportFile('/api/export/docx', store.payload), '论文工坊_论文初稿.docx') }
  catch (err) { alert(err.message) }
}
async function exportMd() {
  if (!store.payload) return
  try { await downloadBlob(await api.exportFile('/api/export/md', store.payload), '论文工坊_论文初稿.md') }
  catch (err) { alert(err.message) }
}
async function copyAll() {
  if (!store.payload) return
  const md = store.payload.chapters
    .map((c) => c.seq > 1 ? '# ' + c.title + '\n\n' + c.content_md : c.content_md)
    .join('\n\n')
    .replace(/!\[([^\]]*)\]\(data:image\/png;base64,[^)]+\)/g, '【已插入图表:$1】')
  try { await navigator.clipboard.writeText(md); alert('全文已复制') }
  catch { alert('复制失败,请手动复制') }
}

function openHistory(item) {
  store.payload = item.payload
  store.view = 'result'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function checkAi() {
  try {
    const data = await api.health()
    if (data.ai_available) {
      store.aiAvailable = true
      store.useAi = true
    }
  } catch { /* 保持默认 */ }
}
async function loadChartTypes() {
  try {
    const data = await api.chartTypes()
    if (data.types && data.types.length) store.chartTypes = data.types
  } catch { /* 使用内置默认 */ }
}
function syncTopbar() {
  const top = document.querySelector('.sticky-top')
  if (!top) return
  const h = top.offsetHeight + 'px'
  document.documentElement.style.setProperty('--topbar-h', h)
  document.body.style.paddingTop = h
}
function onResize() { syncTopbar() }

onMounted(() => {
  store.history = loadHistory()
  checkAi()
  loadChartTypes()
  syncTopbar()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  clearInterval(store.pollTimer)
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <div>
    <div class="sticky-top">
      <header class="site-header">
        <div class="container header-inner">
          <div class="brand">
            <div class="brand-seal">论</div>
            <div class="brand-text">
              <h1>论文工坊 <span class="brand-en">PaperForge</span></h1>
              <p>毕业设计论文写作辅助系统</p>
            </div>
          </div>
          <div class="header-status">
            <span class="status-dot"></span>
            <span>{{ store.aiAvailable ? '系统服务正常 · 智能写作已启用' : '系统服务正常' }}</span>
          </div>
        </div>
      </header>
      <nav class="site-nav">
        <div class="container nav-inner">
          <a class="active" href="#topicView">论文选题</a>
          <a href="#fillPanel">论文生成</a>
          <a href="#historyWrap">历史记录</a>
          <a href="#siteFooter">关于系统</a>
        </div>
      </nav>
    </div>

    <main class="container layout">
      <aside class="panel form-panel" id="fillPanel">
        <div class="section-title">论文信息填报</div>

        <div class="field-group">
          <div class="field-label">一、论文题目（可选）</div>
          <p class="field-tip">已有想法可直接填写;不确定写什么可留空,交给系统推荐</p>
          <input v-model="store.title" class="text-input" type="text" placeholder="如:基于 SpringBoot 与 Vue 的校园二手交易平台" />
          <div class="field-label small">研究方向（用于推荐,可选）</div>
          <input v-model="store.keywords" class="text-input" type="text" placeholder="如:校园二手交易、宠物领养、医院挂号" />
          <div class="hint-row">
            <span class="hint-label">常用方向:</span>
            <button v-for="kw in ['校园二手交易', '高校图书馆', '医院门诊挂号']" :key="kw" class="hint-chip" type="button"
              @click="store.keywords = kw">{{ kw }}</button>
          </div>
          <button class="btn btn-outline btn-block" type="button" :disabled="store.busy" @click="suggestTopics">一键推荐</button>
        </div>

        <div class="field-group">
          <div class="field-label">二、技术路线</div>
          <p class="field-tip">可多选,支持自定义</p>
          <div class="chips">
            <span v-for="t in TECH_PRESETS" :key="t" class="chip" :class="{ on: isTechOn(t) }" @click="toggleTech(t)">{{ t }}</span>
            <span v-for="t in store.customTechs" :key="'c' + t" class="chip on" @click="toggleTech(t)">{{ t }}</span>
          </div>
          <div class="custom-tech">
            <input v-model="customTech" class="text-input" type="text" placeholder="自定义技术,回车添加" @keydown="onCustomKey" />
            <button class="btn btn-outline" type="button" @click="addCustomTech">添加</button>
          </div>
        </div>

        <div class="field-group">
          <div class="field-label">三、生成设置</div>
          <div class="row-2">
            <div>
              <div class="field-label small">字数档位</div>
              <select v-model="store.wordLevel" class="select">
                <option value="small">约 8000 字</option>
                <option value="medium">约 10000 字</option>
                <option value="large">约 15000 字</option>
              </select>
            </div>
            <div>
              <div class="field-label small">行文风格</div>
              <select v-model="store.style" class="select">
                <option value="严谨学术">严谨学术</option>
                <option value="平实工程">平实工程</option>
              </select>
            </div>
          </div>
          <div class="field-label small">补充需求（可选,论文将按此要求撰写）</div>
          <textarea v-model="store.requirements" class="text-input requirements-input"
            placeholder="例如:重点突出系统安全性、完善数据库设计、增加测试用例与异常处理等内容;不填也可正常生成"></textarea>
          <label class="ai-check">
            <input v-model="store.useAi" type="checkbox" :disabled="!store.aiAvailable" />
            <span>启用智能写作模式（未配置写作服务时自动使用本地模板）</span>
          </label>
        </div>

        <div class="actions">
          <button class="btn btn-outline" type="button" :disabled="store.busy" @click="demo">演示模式</button>
        </div>
        <button class="btn btn-primary btn-block" type="button" :disabled="store.busy" @click="generate">开始生成论文</button>

        <div id="historyWrap" class="history" :class="{ hidden: store.history.length === 0 }">
          <div class="field-label">历史记录（最近 5 次）</div>
          <ul class="history-list">
            <li v-for="(item, i) in store.history" :key="i" @click="openHistory(item)">
              {{ new Date(item.ts).toLocaleString() }} · {{ item.title }}
            </li>
          </ul>
        </div>
      </aside>

      <section class="panel main-panel">
        <div v-if="store.view === 'topic'" id="topicView" class="topic-view">
          <div class="section-title">论文选题</div>
          <div class="view-head">
            <p class="topic-hint">{{ topicHint }}</p>
            <button v-if="store.refreshVisible" class="btn btn-outline" type="button" :disabled="store.busy" @click="suggestTopics">重新生成</button>
          </div>
          <div class="topic-grid">
            <template v-if="store.topics.length">
              <article v-for="(t, i) in store.topics" :key="t.title" class="topic-card"
                :class="{ selected: store.selectedTopic && store.selectedTopic.title === t.title }">
                <span class="topic-badge">备选题目{{ '一二三四五六'.charAt(i) }}</span>
                <h3>{{ t.title }}</h3>
                <div class="topic-techs">
                  <span v-for="x in (t.techs || [])" :key="x" class="topic-tech">{{ x }}</span>
                </div>
                <p class="topic-desc">{{ t.description || '' }}</p>
                <div class="topic-tags">
                  <span v-for="x in (t.tags || [])" :key="x" class="topic-tag">{{ x }}</span>
                </div>
                <button class="btn-select" type="button" @click="selectTopic(t)">选择此题</button>
              </article>
            </template>
            <div v-else class="empty-state">
              <p class="empty-main">暂无备选题目</p>
              <p class="field-tip">填写研究方向与技术路线后,点击「一键推荐」</p>
            </div>
          </div>
          <p v-if="store.topicNote" class="note">{{ store.topicNote }}</p>
          <div v-if="store.selectedTopic" class="topic-footer">
            <div class="selected-bar">
              <span class="selected-label">已选题目</span>
              <span class="selected-text">{{ store.selectedTopic.title }}</span>
              <button class="btn-link" type="button" @click="clearTopic">清除</button>
            </div>
          </div>
        </div>

        <div v-else-if="store.view === 'progress'" class="progress-wrap">
          <div class="progress-meta">
            <span>{{ store.stageText }}</span>
            <span></span>
          </div>
          <div class="progress-bar"><div class="progress-fill" :style="{ width: store.progressPct + '%' }"></div></div>
          <div class="stage-list">
            <span v-for="(name, i) in STAGE_NAMES" :key="name" class="stage"
              :class="{ done: i < store.current, active: i === store.current }">{{ name }}</span>
          </div>
          <div v-if="store.liveDesign" class="design-panel">
            <h3>系统设定(全篇一致的模块 / 角色 / 数据表)</h3>
            <div class="design-row">
              <span v-for="m in (designModules.modules || [])" :key="m.name" class="mini-chip"><b>{{ m.name }}</b> {{ m.desc }}</span>
            </div>
            <div class="design-row">
              角色:
              <span v-for="r in (designModules.roles || [])" :key="r" class="mini-chip">{{ r }}</span>
              &nbsp;&nbsp;数据表:
              <span v-for="t in (designModules.tables || [])" :key="t.name" class="mini-chip">{{ t.name }}({{ t.title }})</span>
            </div>
          </div>
          <div class="chapters">
            <article v-for="c in store.liveChapters" :key="c.seq" :id="'chap-' + c.seq" class="chapter">
              <ChapterCard :chapter="c" @changed="chartChanged" />
            </article>
          </div>
        </div>

        <div v-else-if="store.view === 'result'" class="result">
          <div class="result-head">
            <div>
              <h2>{{ store.payload.title }}</h2>
              <span class="meta">{{ paperMeta }}</span>
            </div>
            <div class="export-actions">
              <button class="btn btn-primary" type="button" @click="exportDocx">导出 Word</button>
              <button class="btn btn-outline" type="button" @click="exportMd">下载 Markdown</button>
              <button class="btn btn-outline" type="button" @click="copyAll">复制全文</button>
            </div>
          </div>
          <p v-if="store.payload.note" class="note">{{ store.payload.note }}</p>

          <div v-if="store.payload.system_design" class="design-panel">
            <h3>系统设定(全篇一致的模块 / 角色 / 数据表)</h3>
            <div class="design-row">
              <span v-for="m in (store.payload.system_design.modules || [])" :key="m.name" class="mini-chip"><b>{{ m.name }}</b> {{ m.desc }}</span>
            </div>
            <div class="design-row">
              角色:
              <span v-for="r in (store.payload.system_design.roles || [])" :key="r" class="mini-chip">{{ r }}</span>
              &nbsp;&nbsp;数据表:
              <span v-for="t in (store.payload.system_design.tables || [])" :key="t.name" class="mini-chip">{{ t.name }}({{ t.title }})</span>
            </div>
          </div>

          <div class="doc-layout">
            <nav class="toc">
              <a v-for="c in resultChapters" :key="c.seq" href="javascript:void(0)" @click="scrollToChapter(c.seq)">{{ c.title }}</a>
            </nav>
            <div class="chapters">
              <article v-for="c in resultChapters" :key="c.seq" :id="'chap-' + c.seq" class="chapter">
                <ChapterCard :chapter="c" @changed="chartChanged" />
              </article>
            </div>
          </div>

          <div class="chart-panel">
            <div class="chart-panel-head">
              <h3>生图清单(填写素材后点击「生成图表」)</h3>
              <div class="chart-add">
                <select v-model="chartTypeSel">
                  <option v-for="t in store.chartTypes" :key="t.type" :value="t.type">{{ t.label }}</option>
                </select>
                <select v-model="chartPosSel">
                  <option v-for="p in CHART_POSITIONS" :key="p" :value="p">{{ p }}</option>
                </select>
                <button class="btn-mini" type="button" @click="addChartItem">添加图表</button>
              </div>
            </div>
            <ChartItem v-for="s in chartList" :key="s.fig + '|' + s.title + '|' + (s.prompt ? 'p' : '')"
              :item="s" :deleteable="store.chartExtras.includes(s)"
              @changed="chartChanged" @delete="deleteChartItem(s)" />
          </div>
        </div>
      </section>
    </main>

    <footer class="site-footer" id="siteFooter">
      <div class="container">
        <p>主办:PaperForge 项目组 · 毕业设计论文写作辅助系统</p>
        <p>系统生成的论文初稿仅供参考,请人工核实后使用 · © 2026 PaperForge</p>
      </div>
    </footer>
  </div>
</template>
