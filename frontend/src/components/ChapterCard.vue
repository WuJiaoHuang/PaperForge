<script setup>
import { computed, ref } from 'vue'
import { store } from '../store'
import { api } from '../api'
import { mdToHtml, saveHistory } from '../utils'

const props = defineProps({
  chapter: { type: Object, required: true },
})
const emit = defineEmits(['changed'])

const editable = computed(() => !!store.payload)
const editing = ref(false)
const editorText = ref('')
const regening = ref(false)
const regenText = ref('')
const working = ref(false)

function enterEdit() {
  editorText.value = props.chapter.content_md
  editing.value = true
}
function cancelEdit() { editing.value = false }
function saveEdit() {
  const idx = store.payload.chapters.findIndex((x) => x.seq === props.chapter.seq)
  if (idx === -1) return
  store.payload.chapters[idx].content_md = editorText.value
  props.chapter.content_md = editorText.value
  editing.value = false
  saveHistory(store.payload)
  emit('changed')
}
function enterRegen() { regenText.value = ''; regening.value = true }
function cancelRegen() { regening.value = false }

async function doRegen() {
  if (!store.payload) return
  working.value = true
  try {
    const res = await api.generateChapter({
      title: store.payload.title,
      techs: store.payload.techs || [],
      word_level: store.payload.level || 'medium',
      style: store.payload.style || '严谨学术',
      use_ai: store.useAi,
      chapter_key: props.chapter.key,
      chapter_title: props.chapter.title,
      hint: props.chapter.hint || '',
      instructions: regenText.value.trim(),
      requirements: store.payload.requirements || '',
      system_design: store.payload.system_design || null,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || '重新生成失败')
    const idx = store.payload.chapters.findIndex((x) => x.seq === props.chapter.seq)
    if (idx !== -1) {
      store.payload.chapters[idx].content_md = data.content_md
      props.chapter.content_md = data.content_md
      saveHistory(store.payload)
      emit('changed')
    }
    if (data.note) alert(data.note)
  } catch (err) {
    alert(err.message)
  } finally {
    working.value = false
    regening.value = false
  }
}
</script>

<template>
  <div class="chapter-card">
    <div class="chapter-head">
      <h2>{{ chapter.title }}</h2>
      <div class="chapter-actions">
        <button class="btn-mini" :disabled="!editable || working" @click="editing ? saveEdit() : enterEdit()">
          {{ editing ? '保存' : '编辑' }}
        </button>
        <button class="btn-mini" :disabled="!editable || working"
          @click="editing ? cancelEdit() : (regening ? cancelRegen() : enterRegen())">
          {{ editing ? '取消' : '重新生成' }}
        </button>
      </div>
    </div>
    <div v-if="regening" class="regen-box">
      <textarea v-model="regenText" class="regen-input"
        placeholder="输入修改意见(可选),例如:精简篇幅、补充数据库设计细节、语气更正式;留空则直接重新生成"></textarea>
      <div class="chapter-actions" style="margin-top:8px">
        <button class="btn-mini" :disabled="working" @click="doRegen">确认生成</button>
      </div>
    </div>
    <textarea v-if="editing" v-model="editorText" class="chapter-editor"></textarea>
    <div v-else class="chapter-body" v-html="mdToHtml(chapter.content_md)"></div>
  </div>
</template>
