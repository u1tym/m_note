<script setup lang="ts">
import { ref, watch } from 'vue'

import type { PartInfo } from '../api/types'
import FilePrintDocument from './FilePrintDocument.vue'

export interface PrintFilePayload {
  fileId: number
  folderName: string
  fileTitle: string
  parts: PartInfo[]
}

const props = defineProps<{
  files: PrintFilePayload[]
  pageBreakBetweenFiles?: boolean
}>()

const emit = defineEmits<{
  ready: []
}>()

const readyFileIndexes = ref(new Set<number>())

function fileIdKey(): string {
  return props.files.map((file) => file.fileId).join(',')
}

function checkReady(): void {
  if (props.files.length === 0) {
    return
  }
  if (readyFileIndexes.value.size >= props.files.length) {
    emit('ready')
  }
}

function onFileReady(index: number): void {
  readyFileIndexes.value = new Set([...readyFileIndexes.value, index])
  checkReady()
}

function resetReadyState(): void {
  readyFileIndexes.value = new Set()
}

watch(
  () => fileIdKey(),
  async () => {
    resetReadyState()
  },
)
</script>

<template>
  <div
    class="multi-file-print"
    :class="{
      'multi-file-print--page-breaks': pageBreakBetweenFiles !== false,
      'multi-file-print--continuous': pageBreakBetweenFiles === false,
    }"
  >
    <FilePrintDocument
      v-for="(file, index) in files"
      :key="file.fileId"
      :folder-name="file.folderName"
      :file-title="file.fileTitle"
      :parts="file.parts"
      @ready="onFileReady(index)"
    />
  </div>
</template>
