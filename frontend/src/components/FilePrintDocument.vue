<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import type { PartInfo } from '../api/types'
import PartPrintList from './PartPrintList.vue'

const props = defineProps<{
  folderName: string
  fileTitle: string
  parts: PartInfo[]
}>()

const emit = defineEmits<{
  ready: []
}>()

const loadedTableIds = ref(new Set<number>())

const tableIds = computed(() =>
  props.parts
    .filter((part) => part.ptype === 'table')
    .map((part) => Number.parseInt(part.data, 10))
    .filter((id) => !Number.isNaN(id)),
)

function checkReady(): void {
  if (tableIds.value.every((id) => loadedTableIds.value.has(id))) {
    emit('ready')
  }
}

function onTableLoaded(tableId: number): void {
  loadedTableIds.value = new Set([...loadedTableIds.value, tableId])
  checkReady()
}

function resetReadyState(): void {
  loadedTableIds.value = new Set()
  if (tableIds.value.length === 0) {
    emit('ready')
  }
}

onMounted(() => {
  resetReadyState()
})

watch(
  () => [props.parts, props.fileTitle] as const,
  () => {
    resetReadyState()
  },
)
</script>

<template>
  <article class="file-print-document">
    <header class="file-print-header">
      <p class="subtitle">{{ folderName }}</p>
      <h1>{{ fileTitle }}</h1>
    </header>
    <PartPrintList :parts="parts" @table-loaded="onTableLoaded" />
  </article>
</template>
