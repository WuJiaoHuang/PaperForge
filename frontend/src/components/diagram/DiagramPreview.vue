<script setup>
import { computed } from 'vue'

const props = defineProps({
  diagram: { type: Object, required: true },
  compact: { type: Boolean, default: false },
})

const nodeBounds = computed(() => {
  const nodes = props.diagram.nodes || []
  if (!nodes.length) return { minX: 0, minY: 0, width: 420, height: 260 }
  const xs = nodes.flatMap((node) => [node.position?.x || 0, (node.position?.x || 0) + (node.size?.width || 180)])
  const ys = nodes.flatMap((node) => [node.position?.y || 0, (node.position?.y || 0) + (node.size?.height || 64)])
  const minX = Math.min(...xs) - 40
  const minY = Math.min(...ys) - 40
  return {
    minX,
    minY,
    width: Math.max(420, Math.max(...xs) - minX + 40),
    height: Math.max(260, Math.max(...ys) - minY + 40),
  }
})

const nodeMap = computed(() => new Map((props.diagram.nodes || []).map((node) => [node.id, node])))
const sequence = computed(() => props.diagram.sequence || { participants: [], messages: [] })
const sequenceMessages = computed(() => [...(sequence.value.messages || [])].sort((a, b) => a.order - b.order))
const usecase = computed(() => props.diagram.usecase || { actors: [], usecases: [], relations: [] })

function center(node) {
  return {
    x: (node.position?.x || 0) + (node.size?.width || 180) / 2,
    y: (node.position?.y || 0) + (node.size?.height || 64) / 2,
  }
}

function participantX(index, total) {
  if (total <= 1) return 210
  return 60 + index * (300 / (total - 1))
}

function actorY(index) {
  return 70 + index * 72
}

function usecaseY(index) {
  return 58 + index * 54
}
</script>

<template>
  <div class="diagram-preview" :class="{ compact }" data-testid="diagram-preview">
    <svg v-if="diagram.type === 'sequence'" viewBox="0 0 420 280" role="img">
      <defs>
        <marker id="preview-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="#2f3a46" />
        </marker>
      </defs>
      <g v-for="(participant, index) in sequence.participants" :key="participant.id">
        <rect :x="participantX(index, sequence.participants.length) - 38" y="18" width="76" height="30" rx="4" class="preview-box" />
        <text :x="participantX(index, sequence.participants.length)" y="38" class="preview-text">{{ participant.name }}</text>
        <line :x1="participantX(index, sequence.participants.length)" y1="50" :x2="participantX(index, sequence.participants.length)" y2="248" class="preview-dash" />
      </g>
      <g v-for="(message, index) in sequenceMessages" :key="message.id">
        <line
          :x1="participantX(sequence.participants.findIndex((item) => item.id === message.from), sequence.participants.length)"
          :x2="participantX(sequence.participants.findIndex((item) => item.id === message.to), sequence.participants.length)"
          :y1="78 + index * 24"
          :y2="78 + index * 24"
          class="preview-line"
          marker-end="url(#preview-arrow)"
        />
        <text
          :x="(participantX(sequence.participants.findIndex((item) => item.id === message.from), sequence.participants.length) + participantX(sequence.participants.findIndex((item) => item.id === message.to), sequence.participants.length)) / 2"
          :y="72 + index * 24"
          class="preview-text small"
        >{{ message.text }}</text>
      </g>
    </svg>

    <svg v-else-if="diagram.type === 'usecase'" viewBox="0 0 420 280" role="img">
      <g v-for="(actor, index) in usecase.actors" :key="actor.id">
        <circle cx="44" :cy="actorY(index)" r="10" class="preview-stroke" />
        <line x1="44" :y1="actorY(index) + 10" x2="44" :y2="actorY(index) + 34" class="preview-line plain" />
        <line x1="25" :y1="actorY(index) + 20" x2="63" :y2="actorY(index) + 20" class="preview-line plain" />
        <line x1="44" :y1="actorY(index) + 34" x2="28" :y2="actorY(index) + 54" class="preview-line plain" />
        <line x1="44" :y1="actorY(index) + 34" x2="60" :y2="actorY(index) + 54" class="preview-line plain" />
        <text x="44" :y="actorY(index) + 70" class="preview-text small">{{ actor.name }}</text>
      </g>
      <rect x="120" y="22" width="260" height="226" rx="6" class="preview-boundary" />
      <text x="250" y="44" class="preview-text">系统边界</text>
      <ellipse
        v-for="(usecaseItem, index) in usecase.usecases"
        :key="usecaseItem.id"
        cx="250"
        :cy="usecaseY(index)"
        rx="82"
        ry="20"
        class="preview-ellipse"
      />
      <text
        v-for="(usecaseItem, index) in usecase.usecases"
        :key="'text_' + usecaseItem.id"
        x="250"
        :y="usecaseY(index) + 4"
        class="preview-text small"
      >{{ usecaseItem.name }}</text>
      <line
        v-for="(relation, index) in usecase.relations"
        :key="index"
        x1="68"
        :y1="actorY(Math.max(0, usecase.actors.findIndex((item) => item.id === relation.actor))) + 20"
        x2="168"
        :y2="usecaseY(Math.max(0, usecase.usecases.findIndex((item) => item.id === relation.usecase)))"
        class="preview-line plain"
      />
    </svg>

    <svg v-else :viewBox="`${nodeBounds.minX} ${nodeBounds.minY} ${nodeBounds.width} ${nodeBounds.height}`" role="img">
      <defs>
        <marker id="preview-node-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="#2f3a46" />
        </marker>
      </defs>
      <line
        v-for="edge in diagram.edges || []"
        :key="edge.id"
        :x1="center(nodeMap.get(edge.source) || {}).x"
        :y1="center(nodeMap.get(edge.source) || {}).y"
        :x2="center(nodeMap.get(edge.target) || {}).x"
        :y2="center(nodeMap.get(edge.target) || {}).y"
        class="preview-line"
        marker-end="url(#preview-node-arrow)"
      />
      <g v-for="node in diagram.nodes || []" :key="node.id">
        <ellipse
          v-if="node.style?.shape === 'database'"
          :cx="center(node).x"
          :cy="center(node).y"
          :rx="(node.size?.width || 180) / 2"
          :ry="(node.size?.height || 64) / 2"
          class="preview-box"
        />
        <rect
          v-else
          :x="node.position?.x || 0"
          :y="node.position?.y || 0"
          :width="node.size?.width || 180"
          :height="node.size?.height || 64"
          :rx="node.style?.shape === 'rounded' ? 8 : 3"
          class="preview-box"
        />
        <text :x="center(node).x" :y="center(node).y + 4" class="preview-text">{{ node.text }}</text>
      </g>
    </svg>
  </div>
</template>
