const DEFAULT_SIZE = { width: 160, height: 56 }

export function createEmptyDiagram({
  id = '',
  title = '未命名图表',
  type = 'generic',
  chapterKey = 'ch4',
  sectionKey = '',
  sortOrder = 0,
  isEnabled = true,
} = {}) {
  const base = {
    id,
    title,
    caption: title,
    type,
    chapterKey,
    sectionKey,
    sortOrder,
    isEnabled,
    version: 1,
    nodes: [],
    edges: [],
    sequence: null,
    usecase: null,
    viewport: { x: 0, y: 0, zoom: 1 },
    metadata: {},
  }
  if (type === 'sequence') {
    base.sequence = {
      participants: [
        { id: 'user', name: '用户' },
        { id: 'frontend', name: '前端' },
        { id: 'backend', name: '后端' },
      ],
      messages: [
        { id: 'msg_1', from: 'user', to: 'frontend', text: '提交请求', order: 1 },
        { id: 'msg_2', from: 'frontend', to: 'backend', text: '调用接口', order: 2 },
      ],
    }
  }
  if (type === 'usecase') {
    base.usecase = {
      actors: [{ id: 'user', name: '用户' }],
      usecases: [{ id: 'uc_1', name: '使用系统' }],
      relations: [{ actor: 'user', usecase: 'uc_1' }],
    }
  }
  return base
}

export function createSampleArchitecture(title = '系统架构图') {
  return {
    title,
    type: 'architecture',
    chapterKey: 'ch4',
    nodes: [
      makeNode('node_vue', 'Vue 前端', 120, 80, 'rounded'),
      makeNode('node_api', 'FastAPI 后端', 120, 200, 'rectangle'),
      makeNode('node_mysql', 'MySQL 数据库', 120, 320, 'database'),
    ],
    edges: [
      makeEdge('edge_vue_api', 'node_vue', 'node_api', 'HTTP'),
      makeEdge('edge_api_mysql', 'node_api', 'node_mysql', 'SQL'),
    ],
    viewport: { x: 80, y: 20, zoom: 1 },
    metadata: { source: 'sample' },
  }
}

export function makeNode(id, text, x = 120, y = 120, shape = 'rectangle') {
  return {
    id,
    type: 'default',
    text,
    position: { x, y },
    size: { ...DEFAULT_SIZE },
    style: { shape },
  }
}

export function makeEdge(id, source, target, text = '') {
  return {
    id,
    source,
    target,
    text,
    type: 'step',
  }
}

export function toVueFlowNodes(nodes = []) {
  return nodes.map((node) => ({
    id: node.id,
    type: 'default',
    position: node.position || { x: 0, y: 0 },
    data: {
      text: node.text || '新节点',
      shape: node.style?.shape || 'rectangle',
    },
    style: {
      width: `${node.size?.width || DEFAULT_SIZE.width}px`,
      height: `${node.size?.height || DEFAULT_SIZE.height}px`,
    },
  }))
}

export function toVueFlowEdges(edges = []) {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.text || '',
    type: edge.type || 'step',
    markerEnd: 'arrowclosed',
  }))
}

export function fromVueFlowNodes(nodes = []) {
  return nodes.map((node) => ({
    id: node.id,
    type: 'default',
    text: node.data?.text || '新节点',
    position: {
      x: Number(node.position?.x || 0),
      y: Number(node.position?.y || 0),
    },
    size: {
      width: parseSize(node.style?.width, DEFAULT_SIZE.width),
      height: parseSize(node.style?.height, DEFAULT_SIZE.height),
    },
    style: {
      shape: node.data?.shape || 'rectangle',
    },
  }))
}

export function fromVueFlowEdges(edges = []) {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    text: edge.label || '',
    type: edge.type || 'step',
  }))
}

export function sanitizeDiagramForSave(diagram, nodes, edges, viewport) {
  return {
    id: diagram.id,
    title: diagram.title,
    type: diagram.type || 'generic',
    chapterKey: diagram.chapterKey || diagram.chapter_key || 'ch4',
    version: diagram.version || 1,
    nodes: fromVueFlowNodes(nodes),
    edges: fromVueFlowEdges(edges),
    viewport: viewport || diagram.viewport || {},
    metadata: diagram.metadata || {},
  }
}

function parseSize(value, fallback) {
  if (typeof value === 'number') return value
  const parsed = Number(String(value || '').replace('px', ''))
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}
