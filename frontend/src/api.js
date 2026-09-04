async function post(url, body) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

async function put(url, body) {
  return fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

async function checkedJson(res, fallback = '请求失败') {
  let data = null
  try { data = await res.json() } catch { data = null }
  if (!res.ok) {
    throw new Error((data && (data.detail || data.error)) || fallback)
  }
  return data
}

export const api = {
  health: () => fetch('/api/health').then((r) => r.json()),
  createPaper: (body) => post('/api/writing/papers', body),
  suggest: (body) => post('/api/topics/suggest', body),
  generateStart: (body) => post('/api/generate/start', body),
  generatePartial: (id) => fetch('/api/generate/partial/' + id).then((r) => r.json()),
  generateResult: (id) => fetch('/api/generate/result/' + id).then((r) => checkedJson(r, '获取生成结果失败')),
  generateChapter: (body) => post('/api/generate/chapter', body),
  chartTypes: () => fetch('/api/charts/types').then((r) => r.json()),
  chartGenerate: (body) => post('/api/charts/generate', body),
  exportFile: (path, payload) => post(path, { payload }),
  createDiagram: (paperId, body) => post('/api/writing/papers/' + paperId + '/diagrams', body),
  listDiagrams: (paperId) => fetch('/api/writing/papers/' + paperId + '/diagrams').then((r) => checkedJson(r, '加载图表失败')),
  getDiagram: (paperId, diagramId) => fetch('/api/writing/papers/' + paperId + '/diagrams/' + diagramId).then((r) => checkedJson(r, '打开图表失败')),
  saveDiagram: (paperId, diagramId, body) => put('/api/writing/papers/' + paperId + '/diagrams/' + diagramId, body),
  deleteDiagram: (paperId, diagramId) => fetch('/api/writing/papers/' + paperId + '/diagrams/' + diagramId, { method: 'DELETE' }).then((r) => checkedJson(r, '删除图表失败')),
}
