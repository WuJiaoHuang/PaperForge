<script setup>
import DiagramEditor from './DiagramEditor.vue'
import SequenceEditor from './SequenceEditor.vue'
import UseCaseEditor from './UseCaseEditor.vue'

defineProps({
  diagram: { type: Object, required: true },
  saving: { type: Boolean, default: false },
})
defineEmits(['save', 'close'])
</script>

<template>
  <SequenceEditor
    v-if="diagram.type === 'sequence'"
    :diagram="diagram"
    :saving="saving"
    @save="$emit('save', $event)"
    @close="$emit('close')"
  />
  <UseCaseEditor
    v-else-if="diagram.type === 'usecase'"
    :diagram="diagram"
    :saving="saving"
    @save="$emit('save', $event)"
    @close="$emit('close')"
  />
  <DiagramEditor
    v-else
    :diagram="diagram"
    :saving="saving"
    @save="$emit('save', $event)"
    @close="$emit('close')"
  />
</template>
