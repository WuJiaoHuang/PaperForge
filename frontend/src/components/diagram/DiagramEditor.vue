<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { VueFlow, Handle, MarkerType, Position, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import {
  fromVueFlowEdges,
  fromVueFlowNodes,
  makeNode,
  sanitizeDiagramForSave,
  toVueFlowEdges,
  toVueFlowNodes,
} from '../../utils/diagramAdapter'
import { layoutDiagram } from '../../utils/diagramLayout'

const props = defineProps({
  diagram: { type: Object, required: true },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['save', 'close', 'delete'])

const nodes = ref([])
const edges = ref([])
const selectedId = ref('')
const selectedKind = ref('')
const layouting = ref(false)
const { getViewport, setViewport } = useVueFlow()

const selectedNode = computed(() => selectedKind.value === 'node' ? nodes.value.find((node) => node.id === selectedId.value) : null)
const selectedEdge = computed(() => selectedKind.value === 'edge' ? edges.value.find((edge) => edge.id === selectedId.value) : null)

watch(
  () => props.diagram,
  async (diagram) => {
    nodes.value = toVueFlowNodes(diagram.nodes || [])
    edges.value = toVueFlowEdges(diagram.edges || [])
    selectedId.value = ''
    selectedKind.value = ''
    await nextTick()
    if (diagram.viewport) setViewport(diagram.viewport)
  },
  { immediate: true, deep: true },
)

function selectNode(event) {
  selectedKind.value = 'node'
  selectedId.value = event.node.id
}

function selectNodeById(id) {
  selectedKind.value = 'node'
  selectedId.value = id
}

function selectEdge(event) {
  selectedKind.value = 'edge'
  selectedId.value = event.edge.id
}

function clearSelection() {
  selectedKind.value = ''
  selectedId.value = ''
}

function addNode(shape = 'rectangle') {
  const count = nodes.value.length + 1
  const id = 'node_' + Date.now().toString(36) + '_' + count
  const column = Math.floor((count - 1) / 4)
  const row = (count - 1) % 4
  const node = makeNode(id, shape === 'database' ? '数据表' : '新节点', 120 + column * 180, 120 + row * 130, shape)
  nodes.value = toVueFlowNodes([...fromVueFlowNodes(nodes.value), node])
  selectedKind.value = 'node'
  selectedId.value = id
}

function onConnect(params) {
  const id = 'edge_' + Date.now().toString(36)
  edges.value = [
    ...edges.value,
    {
      id,
      source: params.source,
      target: params.target,
      label: '',
      type: 'step',
      markerEnd: { type: MarkerType.ArrowClosed },
    },
  ]
  selectedKind.value = 'edge'
  selectedId.value = id
}

function updateNodeText(value) {
  if (!selectedNode.value) return
  selectedNode.value.data = { ...selectedNode.value.data, text: value }
}

function updateNodeShape(value) {
  if (!selectedNode.value) return
  selectedNode.value.data = { ...selectedNode.value.data, shape: value }
}

function updateNodeSize(field, value) {
  if (!selectedNode.value) return
  const numeric = Math.max(field === 'width' ? 80 : 40, Number(value) || 0)
  selectedNode.value.style = { ...selectedNode.value.style, [field]: `${numeric}px` }
}

function updateEdgeText(value) {
  if (!selectedEdge.value) return
  selectedEdge.value.label = value
}

function deleteSelection() {
  if (selectedKind.value === 'node' && selectedId.value) {
    const id = selectedId.value
    nodes.value = nodes.value.filter((node) => node.id !== id)
    edges.value = edges.value.filter((edge) => edge.source !== id && edge.target !== id)
  } else if (selectedKind.value === 'edge' && selectedId.value) {
    edges.value = edges.value.filter((edge) => edge.id !== selectedId.value)
  }
  clearSelection()
}

async function autoLayout() {
  layouting.value = true
  try {
    const nextNodes = await layoutDiagram(fromVueFlowNodes(nodes.value), fromVueFlowEdges(edges.value), { type: props.diagram.type })
    nodes.value = toVueFlowNodes(nextNodes)
    setViewport({ x: 40, y: 40, zoom: 1 })
    clearSelection()
  } finally {
    layouting.value = false
  }
}

function save() {
  emit('save', sanitizeDiagramForSave(props.diagram, nodes.value, edges.value, getViewport()))
}

function onKeydown(event) {
  if (event.key !== 'Delete' && event.key !== 'Backspace') return
  const target = event.target
  if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return
  deleteSelection()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <section class="diagram-editor" data-testid="diagram-editor">
    <header class="diagram-editor-head">
      <div>
        <div class="section-title">{{ diagram.title }}</div>
        <p class="field-tip">版本 {{ diagram.version || 1 }} · {{ diagram.type || 'generic' }}</p>
      </div>
      <div class="diagram-head-actions">
        <button class="btn btn-outline" type="button" @click="$emit('close')">返回</button>
        <button class="btn btn-outline" type="button" :disabled="layouting" data-testid="auto-layout" @click="autoLayout">
          {{ layouting ? '布局中' : '自动布局' }}
        </button>
        <button class="btn btn-primary" type="button" :disabled="saving" data-testid="save-diagram" @click="save">
          {{ saving ? '保存中' : '保存' }}
        </button>
      </div>
    </header>

    <div class="diagram-shell">
      <aside class="diagram-toolbar">
        <button class="btn-mini" type="button" data-testid="add-rectangle" @click="addNode('rectangle')">+ 普通模块</button>
        <button class="btn-mini" type="button" data-testid="add-database" @click="addNode('database')">+ 数据库</button>
        <button class="btn-mini" type="button" data-testid="add-decision" @click="addNode('decision')">+ 判断</button>
        <button class="btn-mini danger" type="button" data-testid="delete-selection" :disabled="!selectedId" @click="deleteSelection">删除</button>
      </aside>

      <div class="diagram-canvas" data-testid="diagram-canvas">
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :snap-to-grid="true"
          :snap-grid="[20, 20]"
          :default-edge-options="{ type: 'step', markerEnd: { type: MarkerType.ArrowClosed } }"
          fit-view-on-init
          @node-click="selectNode"
          @edge-click="selectEdge"
          @pane-click="clearSelection"
          @connect="onConnect"
        >
          <Background :gap="20" />
          <Controls />
          <template #node-default="{ id, data, selected }">
            <div class="diagram-node" :class="['shape-' + (data.shape || 'rectangle'), { selected }]" @click.stop="selectNodeById(id)">
              <Handle type="target" :position="Position.Top" />
              <div class="diagram-node-text">{{ data.text }}</div>
              <Handle type="source" :position="Position.Bottom" />
            </div>
          </template>
        </VueFlow>
      </div>

      <aside class="diagram-properties">
        <template v-if="selectedNode">
          <div class="field-label">节点属性</div>
          <label class="diagram-field">
            <span>文字</span>
            <textarea
              class="text-input"
              rows="4"
              data-testid="node-text"
              :value="selectedNode.data.text"
              @input="updateNodeText($event.target.value)"
            ></textarea>
          </label>
          <label class="diagram-field">
            <span>形状</span>
            <select class="select" data-testid="node-shape" :value="selectedNode.data.shape" @change="updateNodeShape($event.target.value)">
              <option value="rectangle">rectangle</option>
              <option value="rounded">rounded</option>
              <option value="database">database</option>
              <option value="decision">decision</option>
            </select>
          </label>
          <div class="diagram-size-row">
            <label class="diagram-field">
              <span>宽度</span>
              <input class="text-input" type="number" min="80" data-testid="node-width" :value="parseInt(selectedNode.style.width)" @input="updateNodeSize('width', $event.target.value)" />
            </label>
            <label class="diagram-field">
              <span>高度</span>
              <input class="text-input" type="number" min="40" data-testid="node-height" :value="parseInt(selectedNode.style.height)" @input="updateNodeSize('height', $event.target.value)" />
            </label>
          </div>
        </template>

        <template v-else-if="selectedEdge">
          <div class="field-label">连线属性</div>
          <label class="diagram-field">
            <span>文字</span>
            <input class="text-input" type="text" data-testid="edge-text" :value="selectedEdge.label" @input="updateEdgeText($event.target.value)" />
          </label>
          <button class="btn-mini danger" type="button" data-testid="delete-edge" @click="deleteSelection">删除连线</button>
        </template>

        <div v-else class="diagram-empty-props">
          <div class="field-label">属性面板</div>
          <p class="field-tip">选择节点或连线后编辑文字、形状和尺寸。</p>
        </div>
      </aside>
    </div>
  </section>
</template>
