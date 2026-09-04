import ELK from 'elkjs/lib/elk.bundled.js'

const elk = new ELK()

const DIRECTION_BY_TYPE = {
  architecture: 'DOWN',
  module: 'DOWN',
  flow: 'DOWN',
  er: 'RIGHT',
}

export async function layoutDiagram(nodes = [], edges = [], options = {}) {
  const direction = options.direction || DIRECTION_BY_TYPE[options.type] || 'DOWN'
  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': direction,
      'elk.spacing.nodeNode': '40',
      'elk.layered.spacing.nodeNodeBetweenLayers': '70',
      'elk.edgeRouting': 'ORTHOGONAL',
    },
    children: nodes.map((node) => ({
      id: node.id,
      width: Number(node.size?.width || 180),
      height: Number(node.size?.height || 64),
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  }

  const result = await elk.layout(graph)
  const positions = new Map((result.children || []).map((node) => [node.id, { x: node.x || 0, y: node.y || 0 }]))
  return nodes.map((node) => ({
    ...node,
    position: positions.get(node.id) || node.position || { x: 0, y: 0 },
  }))
}

export async function layoutDiagramDocument(diagram) {
  const nodes = await layoutDiagram(diagram.nodes || [], diagram.edges || [], { type: diagram.type })
  return {
    ...diagram,
    nodes,
    viewport: { x: 40, y: 40, zoom: 1 },
  }
}
