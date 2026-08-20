<script setup>
import { onMounted, ref } from 'vue'
import { store } from '../store'
import { api } from '../api'
import { blobToBase64, defaultChartPrompt, inferChartType, saveHistory } from '../utils'

const props = defineProps({
  item: { type: Object, required: true },
  deleteable: { type: Boolean, default: false },
})
const emit = defineEmits(['changed', 'delete'])

const material = ref('')
const loading = ref(false)
const error = ref('')
const b64 = ref('')

onMounted(() => { material.value = defaultChartPrompt(props.item) })

async function generate() {
  loading.value = true
  error.value = ''
  b64.value = ''
  try {
    const res = await api.chartGenerate({
      chart_type: inferChartType(props.item),
      title: props.item.title,
      material: material.value.trim(),
      techs: store.payload ? store.payload.techs || [] : [],
      use_ai: store.useAi,
      system_design: store.payload ? store.payload.system_design : null,
    })
    if (!res.ok) {
      let msg = '生成失败'
      try { const d = await res.json(); msg = d.error || msg } catch { /* ignore */ }
      throw new Error(msg)
    }
    b64.value = await blobToBase64(await res.blob())
    const key = (props.item.fig || 'chart') + '|' + (props.item.title || '')
    store.chartImages = store.chartImages || {}
    store.chartImages[key] = b64.value
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function place() {
  if (!store.payload || !b64.value) return
  const s = props.item
  const imgLine = '![' + (s.fig || '图') + ' ' + (s.title || '') + '](data:image/png;base64,' + b64.value + ')'
  const figMatch = (s.fig || '').match(/图\s*\d+\s*[-－]\s*\d+/)
  const figNum = figMatch ? figMatch[0].replace(/\s+/g, ' ').replace('－', '-') : ''
  let placed = false
  store.payload.chapters.forEach((ch) => {
    if (placed) return
    const lines = ch.content_md.split('\n')
    const out = []
    for (const line of lines) {
      if (!placed && figNum && line.includes(figNum) && line.includes('此处建议插入')) {
        out.push(imgLine)
        placed = true
      } else {
        out.push(line)
      }
    }
    ch.content_md = out.join('\n')
  })
  if (!placed) {
    const pos = s.position || ''
    const m = pos.match(/第\s*(\d)\s*章/)
    let target = null
    if (m) target = store.payload.chapters.find((x) => x.key === 'ch' + m[1])
    if (!target && pos.includes('文末')) target = store.payload.chapters[store.payload.chapters.length - 1]
    if (!target) target = store.payload.chapters[store.payload.chapters.length - 1]
    target.content_md = (target.content_md.trimEnd() + '\n\n' + imgLine).trim()
  }
  saveHistory(store.payload)
  emit('changed')
  alert('图片已放入论文' + (figNum ? '对应占位处' : '指定章节'))
}
</script>

<template>
  <div class="chart-item">
    <div class="chart-item-head">
      <span class="chart-fig">{{ item.fig || '新增' }}</span>
      <b>{{ item.title || '' }}</b>
      <span class="chart-pos">{{ item.position || '自定义图表' }}</span>
    </div>
    <textarea v-model="material" class="chart-material" rows="2"></textarea>
    <div class="chart-item-actions">
      <button class="btn-mini" :disabled="loading" @click="generate">生成图表</button>
      <button v-if="deleteable" class="btn-mini" @click="$emit('delete')">删除</button>
    </div>
    <div class="chart-result">
      <span v-if="loading" class="chart-loading">正在绘制…</span>
      <span v-else-if="error" class="chart-error">{{ error }}</span>
      <template v-else-if="b64">
        <img class="chart-img" :src="'data:image/png;base64,' + b64" :alt="item.title || ''" />
        <div class="chart-download">
          <a class="btn-mini" :href="'data:image/png;base64,' + b64"
            :download="(item.fig || 'chart') + '_' + (item.title || '') + '.png'">下载图片</a>
          <button class="btn-mini" @click="place">放入论文指定位置</button>
        </div>
      </template>
    </div>
  </div>
</template>
