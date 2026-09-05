<script setup>
import { computed, ref, watch } from 'vue'
import DiagramPreview from './DiagramPreview.vue'

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

const relations = computed(() => draft.value.usecase.relations)

function makeDraft(diagram) {
  return JSON.parse(JSON.stringify({
    ...diagram,
    usecase: {
      actors: diagram.usecase?.actors?.length ? diagram.usecase.actors : [{ id: 'user', name: '用户' }],
      usecases: diagram.usecase?.usecases?.length ? diagram.usecase.usecases : [{ id: 'uc_1', name: '使用系统' }],
      relations: diagram.usecase?.relations?.length ? diagram.usecase.relations : [{ actor: 'user', usecase: 'uc_1' }],
    },
  }))
}

function addActor() {
  draft.value.usecase.actors.push({ id: 'actor_' + Date.now().toString(36), name: '参与者' })
}

function removeActor(id) {
  if (draft.value.usecase.actors.length <= 1) return
  draft.value.usecase.actors = draft.value.usecase.actors.filter((item) => item.id !== id)
  draft.value.usecase.relations = draft.value.usecase.relations.filter((item) => item.actor !== id)
}

function addUsecase() {
  draft.value.usecase.usecases.push({ id: 'uc_' + Date.now().toString(36), name: '业务功能' })
}

function removeUsecase(id) {
  if (draft.value.usecase.usecases.length <= 1) return
  draft.value.usecase.usecases = draft.value.usecase.usecases.filter((item) => item.id !== id)
  draft.value.usecase.relations = draft.value.usecase.relations.filter((item) => item.usecase !== id)
}

function addRelation() {
  const actor = draft.value.usecase.actors[0]?.id
  const usecase = draft.value.usecase.usecases[0]?.id
  if (!actor || !usecase) return
  draft.value.usecase.relations.push({ actor, usecase })
}

function removeRelation(index) {
  draft.value.usecase.relations.splice(index, 1)
}

function save() {
  emit('save', {
    ...draft.value,
    nodes: [],
    edges: [],
    sequence: null,
    usecase: draft.value.usecase,
  })
}
</script>

<template>
  <section class="diagram-editor usecase-editor" data-testid="usecase-editor">
    <header class="diagram-editor-head">
      <div>
        <div class="section-title">{{ draft.title }}</div>
        <p class="field-tip">编辑图表 · usecase · 版本 {{ draft.version || 1 }}</p>
      </div>
      <div class="diagram-head-actions">
        <button class="btn btn-outline" type="button" @click="$emit('close')">返回</button>
        <button class="btn btn-primary" type="button" :disabled="saving" data-testid="save-diagram" @click="save">
          {{ saving ? '保存中' : '保存' }}
        </button>
      </div>
    </header>

    <div class="structured-preview-layout">
      <div class="structured-edit-stack">
        <section class="structured-panel">
          <div class="chart-panel-head">
            <h3>参与者</h3>
            <button class="btn-mini" type="button" data-testid="add-actor" @click="addActor">新增</button>
          </div>
          <article v-for="actor in draft.usecase.actors" :key="actor.id" class="structured-row">
            <input v-model="actor.name" class="text-input" data-testid="actor-name" />
            <button class="btn-mini danger" type="button" @click="removeActor(actor.id)">删除</button>
          </article>
        </section>

        <section class="structured-panel">
          <div class="chart-panel-head">
            <h3>用例</h3>
            <button class="btn-mini" type="button" data-testid="add-usecase" @click="addUsecase">新增</button>
          </div>
          <article v-for="usecase in draft.usecase.usecases" :key="usecase.id" class="structured-row">
            <input v-model="usecase.name" class="text-input" data-testid="usecase-name" />
            <button class="btn-mini danger" type="button" @click="removeUsecase(usecase.id)">删除</button>
          </article>
        </section>

        <section class="structured-panel">
          <div class="chart-panel-head">
            <h3>关联</h3>
            <button class="btn-mini" type="button" data-testid="add-relation" @click="addRelation">新增</button>
          </div>
          <article v-for="(relation, index) in relations" :key="index" class="relation-row">
            <select v-model="relation.actor" class="select" data-testid="relation-actor">
              <option v-for="actor in draft.usecase.actors" :key="actor.id" :value="actor.id">{{ actor.name }}</option>
            </select>
            <select v-model="relation.usecase" class="select" data-testid="relation-usecase">
              <option v-for="usecase in draft.usecase.usecases" :key="usecase.id" :value="usecase.id">{{ usecase.name }}</option>
            </select>
            <button class="btn-mini danger" type="button" @click="removeRelation(index)">删除</button>
          </article>
        </section>
      </div>

      <aside class="structured-preview-panel">
        <div class="field-label">实时预览</div>
        <DiagramPreview :diagram="draft" />
      </aside>
    </div>
  </section>
</template>
