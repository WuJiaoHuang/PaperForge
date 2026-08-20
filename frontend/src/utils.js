import { store, HISTORY_KEY } from './store'

export function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function inlineMd(s) {
  return escapeHtml(s)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}

export function mdToHtml(md) {
  const lines = String(md || '').split('\n')
  let html = ''
  let listType = null
  let inCode = false
  let codeBuf = []
  let tableBuf = []

  const closeList = () => {
    if (listType) { html += listType === 'ul' ? '</ul>' : '</ol>'; listType = null }
  }
  const flushTable = () => {
    if (!tableBuf.length) return
    const rows = tableBuf.map((r) => r.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim()))
    const header = rows[0]
    const body = rows.filter((r, i) => i > 0 && !/^[\s:\-|]+$/.test(rows[i].join('')))
    html += '<table><thead><tr>' + header.map((c) => '<th>' + inlineMd(c) + '</th>').join('') + '</tr></thead><tbody>'
    body.forEach((r) => { html += '<tr>' + r.map((c) => '<td>' + inlineMd(c) + '</td>').join('') + '</tr>' })
    html += '</tbody></table>'
    tableBuf = []
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    const imgMatch = line.match(/^!\[(.*?)\]\((data:image\/png;base64,[^)]+)\)$/)
    if (imgMatch) {
      closeList(); flushTable()
      html += '<figure class="paper-figure"><img src="' + imgMatch[2] + '" alt="' + escapeHtml(imgMatch[1]) +
        '"/><figcaption>' + escapeHtml(imgMatch[1]) + '</figcaption></figure>'
      continue
    }
    if (line.startsWith('```')) {
      if (!inCode) { closeList(); flushTable(); inCode = true; codeBuf = [] }
      else { html += '<pre><code>' + escapeHtml(codeBuf.join('\n')) + '</code></pre>'; inCode = false }
      continue
    }
    if (inCode) { codeBuf.push(line); continue }
    if (line.startsWith('|')) { closeList(); tableBuf.push(line); continue }
    flushTable()
    if (line.startsWith('### ')) { closeList(); html += '<h3>' + inlineMd(line.slice(4)) + '</h3>' }
    else if (line.startsWith('## ')) { closeList(); html += '<h3>' + inlineMd(line.slice(3)) + '</h3>' }
    else if (line.startsWith('# ')) { closeList(); html += '<h3>' + inlineMd(line.slice(2)) + '</h3>' }
    else if (/^\s*[-*]\s+/.test(line)) {
      if (listType !== 'ul') { closeList(); html += '<ul>'; listType = 'ul' }
      html += '<li>' + inlineMd(line.replace(/^\s*[-*]\s+/, '')) + '</li>'
    } else if (/^\s*\d+[.、]\s+/.test(line)) {
      if (listType !== 'ol') { closeList(); html += '<ol>'; listType = 'ol' }
      html += '<li>' + inlineMd(line.replace(/^\s*\d+[.、]\s+/, '')) + '</li>'
    } else if (line.includes('【此处建议插入')) {
      closeList(); html += '<div class="placeholder">' + inlineMd(line) + '</div>'
    } else if (line.startsWith('>')) {
      closeList(); html += '<p class="note">' + inlineMd(line.replace(/^>\s?/, '')) + '</p>'
    } else if (line.trim()) {
      closeList(); html += '<p>' + inlineMd(line) + '</p>'
    }
  }
  closeList(); flushTable()
  if (inCode) html += '<pre><code>' + escapeHtml(codeBuf.join('\n')) + '</code></pre>'
  return html
}

export function inferChartType(s) {
  if (s && s.type) return s.type
  const t = ((s && s.title) || '') + ((s && s.material) || '')
  if (t.includes('架构')) return 'architecture'
  if (t.includes('用例')) return 'usecase'
  if (t.includes('E-R') || t.includes('ER') || t.includes('实体')) return 'er'
  if (t.includes('流程')) return 'flow'
  if (t.includes('时序')) return 'sequence'
  if (t.includes('模块')) return 'module'
  return 'module'
}

export function chartHint(type) {
  const t = store.chartTypes.find((x) => x.type === type)
  return t ? t.hint : ''
}

export function defaultChartPrompt(s) {
  if (s && s.prompt) return s.prompt
  const p = store.payload
  const title = p ? p.title : ''
  const techs = p && p.techs && p.techs.length ? p.techs.join('、') : ''
  const design = p ? p.system_design : null
  const tables = design && design.tables ? design.tables.map((t) => (t.name || '') + '(' + (t.title || '') + ')').join('、') : ''
  const modules = design && design.modules ? design.modules.map((m) => m.name).join('、') : ''
  const roles = design && design.roles ? design.roles.join('、') : ''
  const features = design && design.features
    ? design.features.map((f) => (typeof f === 'string' ? f : f.desc)).join('、')
    : ''
  const flowSteps = design && design.features && design.features.length
    ? design.features.slice(0, 3).map((f) => (typeof f === 'string' ? f : (f.desc || f.module || '')).slice(0, 14)).join('\n')
    : '用户发起请求\n系统校验与业务处理\n读写数据库'
  const type = inferChartType(s)
  switch (type) {
    case 'er':
      return '请根据以下系统数据表绘制 E-R 图。\n论文题目:' + title + '\n数据表:' + (tables || '系统数据表') +
        '\n(可粘贴 SQL 建表语句替换,系统将解析生成实体与关系)'
    case 'flow':
      return '请根据以下业务流程绘制流程图。\n论文题目:' + title + '\n用户登录系统\n' + flowSteps + '\n数据保存与结果返回'
    case 'architecture':
      return '请根据以下技术栈绘制系统架构图。\n技术栈:' + (techs || '系统技术栈') +
        '\n层次:用户层 → 前端展示层 → 业务逻辑层 → 数据存储层'
    case 'module':
      return '请根据系统功能模块绘制功能模块图。\n论文题目:' + title + '\n模块清单:' + (modules || '用户管理、业务管理、系统管理')
    case 'usecase':
      return '请根据系统角色与功能绘制用例图。\n论文题目:' + title + '\n角色:' + (roles || '管理员、普通用户') +
        '\n功能:' + (features || '登录、业务管理、数据查询')
    case 'sequence':
      return '请根据系统交互流程绘制时序图。\n论文题目:' + title +
        '\n用户 -> 系统: 提交请求\n系统 -> 数据库: 读写数据\n系统 -> 用户: 返回结果'
    default:
      return '请根据论文《' + title + '》绘制所需图表,可按需要修改下方指令。'
  }
}

export function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

export function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]') }
  catch { return [] }
}

export function saveHistory(payload) {
  const list = loadHistory()
  list.unshift({ ts: Date.now(), title: payload.title, payload })
  while (list.length > 5) list.pop()
  localStorage.setItem(HISTORY_KEY, JSON.stringify(list))
  store.history = list
}

export async function downloadBlob(res, name) {
  if (!res.ok) throw new Error('导出失败')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
