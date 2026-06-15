<script setup lang="ts">
import { computed } from 'vue'

import { renderMarkdown } from '../utils/render'

const props = defineProps<{
  source: string
}>()

const html = computed(() => renderMarkdown(props.source))
</script>

<template>
  <div class="md-preview" v-html="html" />
</template>
