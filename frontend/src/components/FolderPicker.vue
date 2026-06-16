<script setup lang="ts">
import type { FlatFolderEntry } from '../api/tree'

defineProps<{
  open: boolean
  title: string
  folders: FlatFolderEntry[]
  excludeIds?: Set<number>
  allowRoot?: boolean
}>()

const emit = defineEmits<{
  pick: [folderId: number | null]
  cancel: []
}>()

function indent(depth: number): string {
  return `${'　'.repeat(depth)}${depth > 0 ? '└ ' : ''}`
}
</script>

<template>
  <div v-if="open" class="picker-overlay" @click.self="emit('cancel')">
    <div class="picker-dialog">
      <h2>{{ title }}</h2>
      <ul class="picker-list">
        <li v-if="allowRoot">
          <button type="button" class="picker-item" @click="emit('pick', null)">
            📁 ルート（最上位）
          </button>
        </li>
        <li v-for="folder in folders" :key="folder.id">
          <button
            type="button"
            class="picker-item"
            :disabled="excludeIds?.has(folder.id)"
            @click="emit('pick', folder.id)"
          >
            {{ indent(folder.depth) }}📁 {{ folder.name }}
          </button>
        </li>
      </ul>
      <p v-if="!allowRoot && folders.length === 0" class="picker-empty">
        移動先フォルダがありません。ツリーでフォルダを展開してください。
      </p>
      <button type="button" class="picker-cancel" @click="emit('cancel')">キャンセル</button>
    </div>
  </div>
</template>
