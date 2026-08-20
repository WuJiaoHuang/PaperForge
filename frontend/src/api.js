async function post(url, body) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export const api = {
  health: () => fetch('/api/health').then((r) => r.json()),
  suggest: (body) => post('/api/topics/suggest', body),
  generateStart: (body) => post('/api/generate/start', body),
  generatePartial: (id) => fetch('/api/generate/partial/' + id).then((r) => r.json()),
  generateResult: (id) => fetch('/api/generate/result/' + id).then((r) => r.json()),
  generateChapter: (body) => post('/api/generate/chapter', body),
  chartTypes: () => fetch('/api/charts/types').then((r) => r.json()),
  chartGenerate: (body) => post('/api/charts/generate', body),
  exportFile: (path, payload) => post(path, { payload }),
}
