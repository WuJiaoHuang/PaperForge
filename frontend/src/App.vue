<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api } from './api'
import { DEFAULT_TECHS, STAGE_NAMES, TECH_PRESETS, store } from './store'
import { downloadBlob, loadHistory, saveHistory } from './utils'
import ChapterCard from './components/ChapterCard.vue'
import DiagramPreview from './components/diagram/DiagramPreview.vue'
import DiagramEditorRouter from './components/diagram/DiagramEditorRouter.vue'
import { createEmptyDiagram, createSampleArchitecture } from './utils/diagramAdapter'
import { layoutDiagramDocument } from './utils/diagramLayout'

const customTech = ref('')
const newFigureType = ref('architecture')
const newFigureTitle = ref('系统架构图')
const newFigureChapterKey = ref('ch4')
const newFigureSectionKey = ref('design_architecture')
const newFigureSortOrder = ref(0)
const figureFilter = ref('all')
const figureAddOpen = ref(false)
const figureMoveTarget = ref(null)
const designShown = ref(false)

const FIGURE_TYPES = [
  { type: 'architecture', title: '系统架构图', chapterKey: 'ch4', sectionKey: 'design_architecture' },
  { type: 'module', title: '功能模块图', chapterKey: 'ch4', sectionKey: 'design_modules' },
  { type: 'flow', title: '业务流程图', chapterKey: 'ch5', sectionKey: 'implementation_flow' },
  { type: 'er', title: 'E-R 图', chapterKey: 'ch4', sectionKey: 'database_design' },
  { type: 'usecase', title: '系统用例图', chapterKey: 'ch3', sectionKey: 'requirements_usecase' },
  { type: 'sequence', title: '业务时序图', chapterKey: 'ch5', sectionKey: 'implementation_sequence' },
]

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
  resetDiagramState()
  store.currentPaperId = ''
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
    store.currentPaperId = start.paper_id || ''
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
      const data = normalizePayload(await api.generateResult(jobId))
      switchCurrentPaper(data)
      saveHistory(data)
      store.stageText = '生成完成'
      store.progressPct = 100
      store.busy = false
      setTimeout(() => {
        store.view = 'result'
        loadDiagrams()
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
const chapterOptions = computed(() => resultChapters.value.map((chapter) => ({
  key: chapter.key,
  title: chapter.title,
  seq: chapter.seq,
})))
const figureSuggestions = computed(() => {
  const suggested = store.payload ? store.payload.chart_suggestions || [] : []
  const mapped = suggested
    .map((item, index) => normalizeSuggestion(item, index))
    .filter((item) => FIGURE_TYPES.some((type) => type.type === item.type))
    .filter((item) => !store.ignoredSuggestionKeys.includes(item.key))
  const missing = FIGURE_TYPES
    .filter((type) => !mapped.some((item) => item.type === type.type))
    .filter((type) => !store.ignoredSuggestionKeys.includes('default_' + type.type))
    .map((type) => ({
      key: 'default_' + type.type,
      type: type.type,
      title: type.title,
      caption: type.title,
      chapterKey: type.chapterKey,
      sectionKey: type.sectionKey,
      sortOrder: 0,
    }))
  return mapped.concat(missing)
})
const figureRows = computed(() => {
  const generatedKeys = new Set(store.diagrams.map((item) => item.type + '|' + (item.chapterKey || '')))
  const suggestions = figureSuggestions.value
    .filter((item) => !generatedKeys.has(item.type + '|' + (item.chapterKey || '')))
    .map((item) => ({ kind: 'suggestion', key: item.key, suggestion: item }))
  const diagrams = sortedDiagrams.value.map((diagram) => ({ kind: 'diagram', key: diagram.id, diagram }))
  return diagrams.concat(suggestions)
})
const filteredFigureRows = computed(() => figureRows.value.filter((row) => {
  if (figureFilter.value === 'all') return true
  if (figureFilter.value === 'recommended') return row.kind === 'suggestion'
  const chapterKey = row.kind === 'diagram' ? row.diagram.chapterKey : row.suggestion.chapterKey
  return chapterKey === figureFilter.value
}))
const figureFilterOptions = computed(() => [
  { key: 'all', label: '全部图表', count: figureRows.value.length },
  { key: 'recommended', label: '系统推荐', count: figureRows.value.filter((row) => row.kind === 'suggestion').length },
  ...chapterOptions.value.map((chapter) => ({
    key: chapter.key,
    label: chapter.title,
    count: figureRows.value.filter((row) => {
      const chapterKey = row.kind === 'diagram' ? row.diagram.chapterKey : row.suggestion.chapterKey
      return chapterKey === chapter.key
    }).length,
  })),
])
const sortedDiagrams = computed(() => [...store.diagrams].sort(compareDiagrams))

function normalizeSuggestion(item, index) {
  const typeInfo = FIGURE_TYPES.find((type) => type.type === item.type) || FIGURE_TYPES[index % FIGURE_TYPES.length]
  return {
    key: (item.type || typeInfo.type) + '_' + index,
    type: item.type || typeInfo.type,
    title: item.title || typeInfo.title,
    caption: item.title || typeInfo.title,
    chapterKey: chapterKeyFromPosition(item.position) || typeInfo.chapterKey,
    sectionKey: typeInfo.sectionKey,
    sortOrder: index,
  }
}

function chapterKeyFromPosition(position) {
  const text = String(position || '')
  if (text.includes('第 3 章') || text.includes('需求')) return 'ch3'
  if (text.includes('第 4 章') || text.includes('设计')) return 'ch4'
  if (text.includes('第 5 章') || text.includes('实现')) return 'ch5'
  if (text.includes('第 6 章') || text.includes('测试')) return 'ch6'
  return ''
}

function figureTypeLabel(type) {
  return FIGURE_TYPES.find((item) => item.type === type)?.title || type
}

function syncNewFigureDefaults() {
  const info = FIGURE_TYPES.find((item) => item.type === newFigureType.value) || FIGURE_TYPES[0]
  newFigureTitle.value = info.title
  newFigureChapterKey.value = info.chapterKey
  newFigureSectionKey.value = info.sectionKey
}

function figureNumber(diagram) {
  const chapter = chapterOptions.value.find((item) => item.key === diagram.chapterKey)
  if (!chapter) return '图'
  const enabled = sortedDiagrams.value.filter((item) => item.isEnabled !== false && item.chapterKey === diagram.chapterKey)
  const index = enabled.findIndex((item) => item.id === diagram.id)
  return index >= 0 ? `图${chapter.seq}-${index + 1}` : `图${chapter.seq}`
}

function placementLabel(diagram) {
  const chapter = chapterOptions.value.find((item) => item.key === diagram.chapterKey)
  return (chapter?.title || diagram.chapterKey || '未设置章节') + (diagram.sectionKey ? ' / ' + sectionLabel(diagram.sectionKey) : '')
}

function sectionLabel(key) {
  const labels = {
    design_architecture: '系统总体架构',
    design_modules: '功能模块设计',
    database_design: '数据库设计',
    implementation_flow: '业务流程实现',
    implementation_sequence: '交互时序设计',
    requirements_usecase: '用例分析',
    custom_flow: '自定义流程',
    ai_check: '智能生成校验',
  }
  return labels[key] || key || '未设置小节'
}

function compareDiagrams(a, b) {
  const chapterA = chapterOptions.value.find((item) => item.key === a.chapterKey)?.seq || 99
  const chapterB = chapterOptions.value.find((item) => item.key === b.chapterKey)?.seq || 99
  if (chapterA !== chapterB) return chapterA - chapterB
  if ((a.sortOrder || 0) !== (b.sortOrder || 0)) return (a.sortOrder || 0) - (b.sortOrder || 0)
  return String(a.createdAt || '').localeCompare(String(b.createdAt || ''))
}
function chapterFigureCount(chapterKey) {
  return store.diagrams.filter((diagram) => diagram.chapterKey === chapterKey && diagram.isEnabled !== false).length
}
function chartChanged() { /* 章节/字数变化由 computed 自动更新 */ }

function resetDiagramState() {
  store.activeDiagram = null
  store.diagramEditorOpen = false
  store.diagrams = []
  store.diagramMessage = ''
  figureAddOpen.value = false
  figureMoveTarget.value = null
  store.ignoredSuggestionKeys = []
}

function normalizePayload(payload) {
  return {
    ...payload,
    paper_id: payload.paper_id || '',
  }
}

function switchCurrentPaper(payload) {
  resetDiagramState()
  store.payload = payload
  store.currentPaperId = payload.paper_id
  loadIgnoredSuggestions()
}

function normalizeDiagram(item) {
  const data = item.data_json || item.data || {}
  return {
    ...data,
    id: item.id || data.id,
    title: item.title || data.title || '未命名图表',
    caption: item.caption || data.caption || item.title || data.title || '未命名图表',
    type: item.type || data.type || 'generic',
    chapterKey: item.chapter_key || data.chapterKey || data.chapter_key || 'ch4',
    sectionKey: item.section_key || data.sectionKey || data.section_key || '',
    sortOrder: Number(item.sort_order ?? data.sortOrder ?? data.sort_order ?? 0),
    isEnabled: item.is_enabled ?? data.isEnabled ?? data.is_enabled ?? true,
    version: item.version || data.version || 1,
    nodes: data.nodes || [],
    edges: data.edges || [],
    sequence: data.sequence || null,
    usecase: data.usecase || null,
    viewport: data.viewport || {},
    metadata: data.metadata || {},
    createdAt: item.created_at || data.createdAt || '',
  }
}

async function loadDiagrams() {
  if (!store.currentPaperId) {
    resetDiagramState()
    store.diagramMessage = '请先创建或生成论文'
    return
  }
  store.diagramLoading = true
  store.diagramMessage = ''
  try {
    const data = await api.listDiagrams(store.currentPaperId)
    store.diagrams = Array.isArray(data) ? data.map(normalizeDiagram) : []
  } catch (err) {
    store.diagramMessage = '图表加载失败:' + err.message
  } finally {
    store.diagramLoading = false
  }
}

async function openDiagramWorkspace() {
  figureFilter.value = 'all'
  store.view = 'diagrams'
  await loadDiagrams()
}

async function openChapterFigures(chapterKey) {
  figureFilter.value = chapterKey || 'all'
  store.view = 'diagrams'
  await loadDiagrams()
}

function openAddFigure() {
  if (!store.currentPaperId) {
    store.diagramMessage = '请先创建或生成论文'
    return
  }
  if (!['all', 'recommended'].includes(figureFilter.value)) {
    newFigureChapterKey.value = figureFilter.value
  }
  figureAddOpen.value = true
}

async function createDiagram(kind = 'blank') {
  if (!store.currentPaperId) {
    resetDiagramState()
    store.diagramMessage = '请先创建或生成论文'
    return
  }
  store.diagramLoading = true
  store.diagramMessage = ''
  try {
    const base = kind === 'sample'
      ? createSampleArchitecture('示例架构图')
      : createEmptyDiagram({
        title: newFigureTitle.value.trim() || figureTypeLabel(newFigureType.value),
        type: newFigureType.value,
        chapterKey: newFigureChapterKey.value,
        sectionKey: newFigureSectionKey.value,
        sortOrder: Number(newFigureSortOrder.value) || 0,
      })
    const res = await api.createDiagram(store.currentPaperId, {
      title: base.title,
      caption: base.caption || base.title,
      type: base.type,
      chapter_key: base.chapterKey,
      section_key: base.sectionKey,
      sort_order: base.sortOrder,
      is_enabled: base.isEnabled,
      data: base,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || data.error || '创建图表失败')
    store.activeDiagram = normalizeDiagram(data)
    store.diagramEditorOpen = true
    figureAddOpen.value = false
    await loadDiagrams()
  } catch (err) {
    store.diagramMessage = err.message
  } finally {
    store.diagramLoading = false
  }
}

async function persistDiagramDocument(document) {
  const res = await api.saveDiagram(store.currentPaperId, document.id, {
    title: document.title,
    caption: document.caption || document.title,
    type: document.type,
    chapter_key: document.chapterKey,
    section_key: document.sectionKey,
    sort_order: Number(document.sortOrder) || 0,
    is_enabled: document.isEnabled !== false,
    data: document,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error || '保存图表失败')
  return normalizeDiagram(data)
}

async function generateAutoDiagram(source = null) {
  if (!store.currentPaperId) {
    resetDiagramState()
    store.diagramMessage = '请先创建或生成论文'
    return
  }
  const config = source || {
    type: newFigureType.value,
    title: newFigureTitle.value.trim() || figureTypeLabel(newFigureType.value),
    caption: newFigureTitle.value.trim() || figureTypeLabel(newFigureType.value),
    chapterKey: newFigureChapterKey.value,
    sectionKey: newFigureSectionKey.value,
    sortOrder: Number(newFigureSortOrder.value) || 0,
  }
  store.diagramLoading = true
  store.diagramMessage = ''
  try {
    const created = normalizeDiagram(await api.generateDiagram(store.currentPaperId, {
      type: config.type,
      title: config.title,
      caption: config.caption || config.title,
      chapter_key: config.chapterKey,
      section_key: config.sectionKey,
      sort_order: Number(config.sortOrder) || 0,
      is_enabled: true,
    }))
    const layouted = await layoutDiagramDocument(created)
    store.activeDiagram = await persistDiagramDocument(layouted)
    store.diagramEditorOpen = true
    figureAddOpen.value = false
    await loadDiagrams()
    store.diagramMessage = '图表已自动生成并完成布局'
  } catch (err) {
    store.diagramMessage = '自动生成失败:' + err.message
  } finally {
    store.diagramLoading = false
  }
}

async function generateFromSuggestion(suggestion) {
  await generateAutoDiagram(suggestion)
}

function ignoreSuggestion(suggestion) {
  if (!store.ignoredSuggestionKeys.includes(suggestion.key)) {
    store.ignoredSuggestionKeys.push(suggestion.key)
    saveIgnoredSuggestions()
  }
}

async function regenerateDiagram(diagram) {
  if (!confirm('重新生成会创建一张新的图表,当前编辑成果会保留。是否继续?')) return
  await generateAutoDiagram({
    type: diagram.type,
    title: diagram.caption || diagram.title,
    caption: diagram.caption || diagram.title,
    chapterKey: diagram.chapterKey,
    sectionKey: diagram.sectionKey,
    sortOrder: (Number(diagram.sortOrder) || 0) + 1,
  })
}

async function openDiagram(item) {
  if (!store.currentPaperId || !item) return
  store.diagramLoading = true
  store.diagramMessage = ''
  try {
    const data = await api.getDiagram(store.currentPaperId, item.id)
    store.activeDiagram = normalizeDiagram(data)
    store.diagramEditorOpen = true
  } catch (err) {
    store.diagramMessage = '图表打开失败:' + err.message
  } finally {
    store.diagramLoading = false
  }
}

async function saveDiagram(document) {
  if (!store.currentPaperId || !store.activeDiagram) return
  store.diagramSaving = true
  store.diagramMessage = ''
  try {
    const res = await api.saveDiagram(store.currentPaperId, store.activeDiagram.id, {
      title: document.title,
      caption: document.caption || document.title,
      type: document.type,
      chapter_key: document.chapterKey,
      section_key: document.sectionKey,
      sort_order: Number(document.sortOrder) || 0,
      is_enabled: document.isEnabled !== false,
      data: document,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || data.error || '保存图表失败')
    store.activeDiagram = normalizeDiagram(data)
    await loadDiagrams()
    store.diagramMessage = '图表已保存'
  } catch (err) {
    store.diagramMessage = err.message
  } finally {
    store.diagramSaving = false
  }
}

async function updateDiagramPlacement(diagram) {
  if (!store.currentPaperId || !diagram) return
  store.diagramSaving = true
  store.diagramMessage = ''
  try {
    const saved = await persistDiagramDocument({
      ...diagram,
      chapterKey: diagram.chapterKey,
      sectionKey: diagram.sectionKey,
      sortOrder: Number(diagram.sortOrder) || 0,
      isEnabled: diagram.isEnabled !== false,
    })
    const index = store.diagrams.findIndex((item) => item.id === saved.id)
    if (index >= 0) store.diagrams[index] = saved
    figureMoveTarget.value = null
    store.diagramMessage = '图表位置已保存'
  } catch (err) {
    store.diagramMessage = '位置保存失败:' + err.message
  } finally {
    store.diagramSaving = false
  }
}

function openMoveFigure(diagram) {
  figureMoveTarget.value = diagram
}

function loadIgnoredSuggestions() {
  if (!store.currentPaperId) return
  try {
    const raw = localStorage.getItem('paperforge_ignored_figures_' + store.currentPaperId)
    store.ignoredSuggestionKeys = raw ? JSON.parse(raw) : []
  } catch {
    store.ignoredSuggestionKeys = []
  }
}

function saveIgnoredSuggestions() {
  if (!store.currentPaperId) return
  localStorage.setItem('paperforge_ignored_figures_' + store.currentPaperId, JSON.stringify(store.ignoredSuggestionKeys))
}

async function deleteDiagram(item) {
  if (!store.currentPaperId || !item) return
  if (!confirm('确认删除该论文图表?')) return
  store.diagramLoading = true
  try {
    await api.deleteDiagram(store.currentPaperId, item.id)
    if (store.activeDiagram && store.activeDiagram.id === item.id) {
      store.activeDiagram = null
      store.diagramEditorOpen = false
    }
    await loadDiagrams()
  } catch (err) {
    store.diagramMessage = '图表删除失败:' + err.message
  } finally {
    store.diagramLoading = false
  }
}

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

async function openHistory(item) {
  const payload = normalizePayload(item.payload)
  switchCurrentPaper(payload)
  store.view = 'result'
  if (store.currentPaperId) await loadDiagrams()
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
          <a href="#diagramWorkspace" @click.prevent="openDiagramWorkspace">论文图表</a>
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

        <div v-else-if="store.view === 'diagrams'" id="diagramWorkspace" class="diagram-workspace">
          <div class="view-head">
            <div>
              <div class="section-title">论文图表</div>
              <p class="topic-hint">统一管理推荐图、已生成图、缩略预览和论文放置位置。</p>
            </div>
            <button class="btn btn-outline" type="button" @click="store.view = store.payload ? 'result' : 'topic'">返回</button>
          </div>
          <div class="diagram-panel" data-testid="diagram-panel">
            <p v-if="store.diagramMessage" class="note">{{ store.diagramMessage }}</p>
            <div v-if="!store.diagramEditorOpen" class="diagram-panel-main">
              <div class="figure-manager">
                <aside class="figure-sidebar">
                  <button
                    v-for="filter in figureFilterOptions"
                    :key="filter.key"
                    class="figure-filter"
                    :class="{ active: figureFilter === filter.key }"
                    type="button"
                    @click="figureFilter = filter.key"
                  >
                    <span>{{ filter.label }}</span>
                    <b>{{ filter.count }}</b>
                  </button>
                </aside>

                <section class="figure-manager-main">
                  <div class="figure-manager-head">
                    <div>
                      <h3>{{ figureFilterOptions.find((item) => item.key === figureFilter)?.label || '全部图表' }}</h3>
                      <p class="field-tip">已生成图显示只读缩略预览，推荐图可直接生成并编辑。</p>
                    </div>
                    <div class="diagram-list-actions">
                      <button class="btn-mini" type="button" :disabled="!store.currentPaperId || store.diagramLoading" @click="loadDiagrams">刷新</button>
                      <button class="btn-mini primary-mini" type="button" data-testid="open-add-figure" :disabled="!store.currentPaperId" @click="openAddFigure">+ 新增图表</button>
                    </div>
                  </div>

                  <div v-if="filteredFigureRows.length" class="figure-card-grid">
                    <article v-for="row in filteredFigureRows" :key="row.key" class="figure-card" :class="{ suggestion: row.kind === 'suggestion' }">
                      <template v-if="row.kind === 'diagram'">
                        <DiagramPreview :diagram="row.diagram" compact />
                        <div class="figure-card-body">
                          <b>{{ figureNumber(row.diagram) }} {{ row.diagram.caption || row.diagram.title }}</b>
                          <span>{{ figureTypeLabel(row.diagram.type) }}</span>
                          <span>{{ placementLabel(row.diagram) }} · 版本 {{ row.diagram.version }}</span>
                        </div>
                        <div class="diagram-list-actions">
                          <button class="btn-mini" type="button" data-testid="open-diagram" @click="openDiagram(row.diagram)">编辑</button>
                          <button class="btn-mini" type="button" @click="openMoveFigure(row.diagram)">移动</button>
                          <button class="btn-mini" type="button" @click="regenerateDiagram(row.diagram)">重新生成</button>
                          <button class="btn-mini danger" type="button" @click="deleteDiagram(row.diagram)">删除</button>
                        </div>
                      </template>
                      <template v-else>
                        <div class="figure-recommend-preview">{{ figureTypeLabel(row.suggestion.type) }}</div>
                        <div class="figure-card-body">
                          <b>{{ row.suggestion.caption }}</b>
                          <span>系统推荐</span>
                          <span>建议位置：{{ placementLabel(row.suggestion) }}</span>
                        </div>
                        <div class="diagram-list-actions">
                          <button class="btn-mini" type="button" @click="generateFromSuggestion(row.suggestion)">生成并编辑</button>
                          <button class="btn-mini" type="button" @click="ignoreSuggestion(row.suggestion)">忽略</button>
                        </div>
                      </template>
                    </article>
                  </div>
                  <div v-else class="empty-state diagram-empty">
                    <p class="empty-main">暂无论文图表</p>
                    <p class="field-tip">可以接受系统推荐，也可以新增自定义图表。</p>
                  </div>
                </section>
              </div>
            </div>

            <DiagramEditorRouter
              v-else-if="store.activeDiagram"
              :diagram="store.activeDiagram"
              :saving="store.diagramSaving"
              @save="saveDiagram"
              @close="store.diagramEditorOpen = false"
            />
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
              <button class="btn btn-outline" type="button" @click="openDiagramWorkspace">论文图表</button>
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
                <div class="chapter-figure-strip">
                  <span>本章图表 {{ chapterFigureCount(c.key) }}</span>
                  <button class="btn-mini" type="button" @click="openChapterFigures(c.key)">管理本章图表</button>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>
    </main>

    <div v-if="figureAddOpen" class="modal-backdrop" data-testid="figure-add-modal">
      <section class="modal-panel">
        <header class="modal-head">
          <div class="section-title">新增图表</div>
          <button class="btn-mini" type="button" @click="figureAddOpen = false">关闭</button>
        </header>
        <div class="modal-grid">
          <label class="diagram-field">
            <span>图表类型</span>
            <select v-model="newFigureType" class="select" data-testid="new-figure-type" @change="syncNewFigureDefaults">
              <option v-for="item in FIGURE_TYPES" :key="item.type" :value="item.type">{{ item.title }}</option>
            </select>
          </label>
          <label class="diagram-field">
            <span>caption</span>
            <input v-model="newFigureTitle" class="text-input" data-testid="new-figure-title" />
          </label>
          <label class="diagram-field">
            <span>章节</span>
            <select v-model="newFigureChapterKey" class="select" data-testid="new-figure-chapter">
              <option v-for="chapter in chapterOptions" :key="chapter.key" :value="chapter.key">{{ chapter.title }}</option>
            </select>
          </label>
          <label class="diagram-field">
            <span>小节</span>
            <input v-model="newFigureSectionKey" class="text-input" :placeholder="sectionLabel(newFigureSectionKey)" />
          </label>
          <label class="diagram-field">
            <span>排序</span>
            <input v-model.number="newFigureSortOrder" class="text-input" type="number" />
          </label>
        </div>
        <footer class="modal-actions">
          <button class="btn btn-primary" type="button" data-testid="generate-diagram" :disabled="store.diagramLoading" @click="generateAutoDiagram()">自动生成并编辑</button>
          <button class="btn btn-outline" type="button" data-testid="create-blank-diagram" :disabled="store.diagramLoading" @click="createDiagram('blank')">创建空白图</button>
        </footer>
      </section>
    </div>

    <div v-if="figureMoveTarget" class="modal-backdrop" data-testid="figure-move-modal">
      <section class="modal-panel small">
        <header class="modal-head">
          <div class="section-title">移动图表</div>
          <button class="btn-mini" type="button" @click="figureMoveTarget = null">关闭</button>
        </header>
        <div class="modal-grid">
          <label class="diagram-field">
            <span>章节</span>
            <select v-model="figureMoveTarget.chapterKey" class="select" data-testid="move-chapter">
              <option v-for="chapter in chapterOptions" :key="chapter.key" :value="chapter.key">{{ chapter.title }}</option>
            </select>
          </label>
          <label class="diagram-field">
            <span>小节</span>
            <input v-model="figureMoveTarget.sectionKey" class="text-input" data-testid="move-section" />
          </label>
          <label class="diagram-field">
            <span>顺序</span>
            <input v-model.number="figureMoveTarget.sortOrder" class="text-input" data-testid="move-order" type="number" />
          </label>
          <label class="inline-check">
            <input v-model="figureMoveTarget.isEnabled" type="checkbox" />
            纳入论文
          </label>
        </div>
        <footer class="modal-actions">
          <button class="btn btn-primary" type="button" data-testid="save-move" :disabled="store.diagramSaving" @click="updateDiagramPlacement(figureMoveTarget)">保存位置</button>
        </footer>
      </section>
    </div>

    <footer class="site-footer" id="siteFooter">
      <div class="container">
        <p>主办:PaperForge 项目组 · 毕业设计论文写作辅助系统</p>
        <p>系统生成的论文初稿仅供参考,请人工核实后使用 · © 2026 PaperForge</p>
      </div>
    </footer>
  </div>
</template>
