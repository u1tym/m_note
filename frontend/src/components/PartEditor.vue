<script setup lang="ts">
import { ref } from 'vue'

import type { PartInfo, PartsType } from '../api/types'
import MarkdownPreview from './MarkdownPreview.vue'
import TexPreview from './TexPreview.vue'

defineProps<{
  parts: PartInfo[]
}>()

const emit = defineEmits<{
  add: [type: PartsType, data: string]
  update: [part: PartInfo, type: PartsType, data: string]
  delete: [partsId: number]
}>()

const newType = ref<PartsType>('text')
const newData = ref('')
const previewEnabled = ref<Record<number, boolean>>({})

const partTypeOptions: { value: PartsType; label: string }[] = [
  { value: 'text', label: 'テキスト' },
  { value: 'md', label: 'Markdown' },
  { value: 'tex', label: 'TeX' },
  { value: 'url', label: 'URL' },
  { value: 'jpeg', label: 'JPEG（Base64）' },
  { value: 'png', label: 'PNG（Base64）' },
  { value: 'binary', label: 'バイナリ（Base64）' },
]

function isBinaryType(type: PartsType): boolean {
  return type === 'jpeg' || type === 'png' || type === 'binary'
}

function hasPreview(type: PartsType): boolean {
  return type === 'md' || type === 'tex'
}

function togglePreview(partId: number): void {
  previewEnabled.value[partId] = !previewEnabled.value[partId]
}

function isPreviewOn(partId: number): boolean {
  return previewEnabled.value[partId] ?? true
}

async function onPickBinaryFile(): Promise<void> {
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept =
      newType.value === 'jpeg' ? 'image/jpeg' : newType.value === 'png' ? 'image/png' : '*/*'
    input.onchange = async () => {
      const file = input.files?.[0]
      if (!file) {
        resolve()
        return
      }
      const buffer = await file.arrayBuffer()
      const bytes = new Uint8Array(buffer)
      let binary = ''
      for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]!)
      }
      newData.value = btoa(binary)
      resolve()
    }
    input.click()
  })
}

async function onAdd(): Promise<void> {
  if (isBinaryType(newType.value) && !newData.value) {
    await onPickBinaryFile()
  }
  if (!newData.value && newType.value !== 'text') {
    return
  }
  emit('add', newType.value, newData.value)
  newData.value = ''
}

function onDeletePart(partsId: number): void {
  if (!window.confirm('このパーツを削除しますか？（論理削除）')) {
    return
  }
  emit('delete', partsId)
}

function partLabel(ptype: PartsType): string {
  return partTypeOptions.find((o) => o.value === ptype)?.label ?? ptype
}
</script>

<template>
  <section class="parts-panel">
    <ul class="parts-list">
      <li v-for="part in parts" :key="part.id" class="part-card">
        <div class="part-header">
          <span class="part-type">{{ partLabel(part.ptype) }}</span>
          <div class="part-header-actions">
            <button
              v-if="hasPreview(part.ptype)"
              type="button"
              @click="togglePreview(part.id)"
            >
              {{ isPreviewOn(part.id) ? 'プレビュー非表示' : 'プレビュー表示' }}
            </button>
            <button type="button" class="danger" @click="onDeletePart(part.id)">削除</button>
          </div>
        </div>

        <template v-if="part.ptype === 'jpeg' || part.ptype === 'png'">
          <img
            class="part-image"
            :src="`data:image/${part.ptype};base64,${part.data}`"
            :alt="`part-${part.id}`"
          />
        </template>
        <template v-else-if="part.ptype === 'url'">
          <a :href="part.data" target="_blank" rel="noopener noreferrer">{{ part.data }}</a>
        </template>
        <template v-else-if="part.ptype === 'binary'">
          <p class="binary-hint">バイナリデータ（{{ part.data.length }} 文字の Base64）</p>
        </template>
        <template v-else>
          <textarea
            class="part-text"
            :value="part.data"
            rows="4"
            @change="
              emit(
                'update',
                part,
                part.ptype,
                ($event.target as HTMLTextAreaElement).value,
              )
            "
          />
          <div v-if="hasPreview(part.ptype) && isPreviewOn(part.id)" class="part-preview">
            <p class="preview-label">プレビュー</p>
            <MarkdownPreview v-if="part.ptype === 'md'" :source="part.data" />
            <TexPreview v-else-if="part.ptype === 'tex'" :source="part.data" />
          </div>
        </template>
      </li>
    </ul>

    <div class="add-part">
      <h2>パーツを追加</h2>
      <select v-model="newType">
        <option v-for="opt in partTypeOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <textarea
        v-if="!isBinaryType(newType)"
        v-model="newData"
        rows="4"
        :placeholder="newType === 'url' ? 'https://...' : '内容を入力'"
      />
      <div v-else class="binary-upload">
        <button type="button" @click="onPickBinaryFile">ファイルを選択</button>
        <span v-if="newData">選択済み（Base64 {{ newData.length }} 文字）</span>
      </div>
      <div v-if="hasPreview(newType) && newData" class="part-preview">
        <p class="preview-label">プレビュー</p>
        <MarkdownPreview v-if="newType === 'md'" :source="newData" />
        <TexPreview v-else-if="newType === 'tex'" :source="newData" />
      </div>
      <button type="button" class="primary" @click="onAdd">追加</button>
    </div>
  </section>
</template>
