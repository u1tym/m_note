<script setup lang="ts">
import katex from 'katex'
import { computed } from 'vue'

const props = defineProps<{
  source: string
}>()

const html = computed(() => {
  try {
    return katex.renderToString(props.source, {
      displayMode: true,
      throwOnError: false,
    })
  } catch {
    return props.source
  }
})
</script>

<template>
  <div class="tex-preview" v-html="html" />
</template>
