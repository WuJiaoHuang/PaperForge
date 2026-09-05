<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  diagram: { type: Object, required: true },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['save', 'close'])

const draft = ref(makeDraft(props.diagram))

watch(
  () => props.diagram,
  (diagram) => {
    draft.value = makeDraft(diagram)
  },
  { deep: true },
)

const orderedMessages = computed(() => [...draft.value.sequence.messages].sort((a, b) => a.order - b.order))

function makeDraft(diagram) {
  return JSON.parse(JSON.stringify({
    ...diagram,
    sequence: {
      participants: diagram.sequence?.participants?.length ? diagram.sequence.participants : [
        { id: 'user', name: '用户' },
        { id: 'system', name: '系统' },
      ],
      messages: diagram.sequence?.messages?.length ? diagram.sequence.messages : [
        { id: 'msg_1', from: 'user', to: 'system', text: '发起请求', order: 1 },
      ],
    },
  }))
}

function addParticipant() {
  const id = 'participant_' + Date.now().toString(36)
  draft.value.sequence.participants.push({ id, name: '参与者' })
}

function removeParticipant(id) {
  if (draft.value.sequence.participants.length <= 2) return
  draft.value.sequence.participants = draft.value.sequence.participants.filter((item) => item.id !== id)
  const fallback = draft.value.sequence.participants[0]?.id || ''
  draft.value.sequence.messages = draft.value.sequence.messages
    .map((message) => ({
      ...message,
      from: message.from === id ? fallback : message.from,
      to: message.to === id ? fallback : message.to,
    }))
    .filter((message) => message.from && message.to)
}

function addMessage() {
  const participants = draft.value.sequence.participants
  const from = participants[0]?.id || ''
  const to = participants[1]?.id || from
  draft.value.sequence.messages.push({
    id: 'msg_' + Date.now().toString(36),
    from,
    to,
    text: '交互消息',
    order: draft.value.sequence.messages.length + 1,
  })
  normalizeOrder()
}

function removeMessage(id) {
  draft.value.sequence.messages = draft.value.sequence.messages.filter((item) => item.id !== id)
  normalizeOrder()
}

function moveMessage(id, delta) {
  const list = orderedMessages.value
  const index = list.findIndex((item) => item.id === id)
  const next = index + delta
  if (index < 0 || next < 0 || next >= list.length) return
  const currentOrder = list[index].order
  list[index].order = list[next].order
  list[next].order = currentOrder
  draft.value.sequence.messages = list
  normalizeOrder()
}

function normalizeOrder() {
  draft.value.sequence.messages = orderedMessages.value.map((item, index) => ({ ...item, order: index + 1 }))
}

function save() {
  normalizeOrder()
  emit('save', {
    ...draft.value,
    nodes: [],
    edges: [],
    sequence: draft.value.sequence,
    usecase: null,
  })
}
</script>

<template>
  <section class="diagram-editor sequence-editor" data-testid="sequence-editor">
    <header class="diagram-editor-head">
      <div>
        <div class="section-title">{{ draft.title }}</div>
        <p class="field-tip">编辑图表 · sequence · 版本 {{ draft.version || 1 }}</p>
      </div>
      <div class="diagram-head-actions">
        <button class="btn btn-outline" type="button" @click="$emit('close')">返回</button>
        <button class="btn btn-primary" type="button" :disabled="saving" data-testid="save-diagram" @click="save">
          {{ saving ? '保存中' : '保存' }}
        </button>
      </div>
    </header>

    <div class="structured-editor-grid">
      <section class="structured-panel">
        <div class="chart-panel-head">
          <h3>参与者</h3>
          <button class="btn-mini" type="button" data-testid="add-participant" @click="addParticipant">新增</button>
        </div>
        <div class="structured-list">
          <article v-for="participant in draft.sequence.participants" :key="participant.id" class="structured-row">
            <input v-model="participant.name" class="text-input" data-testid="participant-name" />
            <button class="btn-mini danger" type="button" @click="removeParticipant(participant.id)">删除</button>
          </article>
        </div>
      </section>

      <section class="structured-panel">
        <div class="chart-panel-head">
          <h3>消息</h3>
          <button class="btn-mini" type="button" data-testid="add-message" @click="addMessage">新增</button>
        </div>
        <div class="structured-list">
          <article v-for="message in orderedMessages" :key="message.id" class="message-row">
            <select v-model="message.from" class="select" data-testid="message-from">
              <option v-for="participant in draft.sequence.participants" :key="participant.id" :value="participant.id">{{ participant.name }}</option>
            </select>
            <select v-model="message.to" class="select" data-testid="message-to">
              <option v-for="participant in draft.sequence.participants" :key="participant.id" :value="participant.id">{{ participant.name }}</option>
            </select>
            <input v-model="message.text" class="text-input" data-testid="message-text" />
            <button class="btn-mini" type="button" @click="moveMessage(message.id, -1)">上移</button>
            <button class="btn-mini" type="button" @click="moveMessage(message.id, 1)">下移</button>
            <button class="btn-mini danger" type="button" @click="removeMessage(message.id)">删除</button>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>
