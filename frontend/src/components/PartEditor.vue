<script setup lang="ts">
import { ref } from 'vue'

import { getPartRevision } from '../api/noteApi'
import type { PartInfo, PartRevisionSummary, PartsType } from '../api/types'
import { formatApiError } from '../api/errors'
import {
  acceptForPartType,
  defaultDownloadName,
  downloadBase64Part,
  formatByteSize,
  mimeTypeForPart,
  pickFile,
  readFileAsBase64,
} from '../utils/binaryPart'
import MarkdownPreview from './MarkdownPreview.vue'
import TexPreview from './TexPreview.vue'

defineProps<{
  parts: PartInfo[]
}>()

const emit = defineEmits<{
  add: [type: PartsType, data: string, filename: string]
  update: [part: PartInfo, type: PartsType, data: string, filename: string]
  delete: [partsId: number]
}>()

const newType = ref<PartsType>('text')
const newData = ref('')
const newFilename = ref('')
const previewEnabled = ref<Record<number, boolean>>({})
const replacingPartId = ref<number | null>(null)
const downloadingRevisionId = ref<number | null>(null)
const localError = ref<string | null>(null)

const partTypeOptions: { value: PartsType; label: string }[] = [
  { value: 'text', label: 'テキスト' },
  { value: 'md', label: 'Markdown' },
  { value: 'tex', label: 'TeX' },
  { value: 'url', label: 'URL' },
  { value: 'jpeg', label: 'JPEG' },
  { value: 'png', label: 'PNG' },
  { value: 'binary', label: 'バイナリ' },
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

async function onPickBinaryFileForNew(): Promise<void> {
  const file = await pickFile(acceptForPartType(newType.value))
  if (!file) {
    return
  }
  newFilename.value = file.name
  newData.value = await readFileAsBase64(file)
}

async function onAdd(): Promise<void> {
  localError.value = null
  if (isBinaryType(newType.value) && !newData.value) {
    await onPickBinaryFileForNew()
  }
  if (!newData.value && newType.value !== 'text') {
    return
  }
  if (isBinaryType(newType.value) && !newFilename.value.trim()) {
    localError.value = 'ファイル名が必要です'
    return
  }
  emit('add', newType.value, newData.value, newFilename.value.trim())
  newData.value = ''
  newFilename.value = ''
}

function onDeletePart(partsId: number): void {
  if (!window.confirm('このパーツを削除しますか？（論理削除）')) {
    return
  }
  emit('delete', partsId)
}

function onDownloadBinaryPart(part: PartInfo): void {
  downloadBase64Part(
    part.data,
    defaultDownloadName(part.id, part.ptype, part.filename),
    mimeTypeForPart(part.ptype),
  )
}

async function onDownloadRevision(revision: PartRevisionSummary): Promise<void> {
  localError.value = null
  downloadingRevisionId.value = revision.id
  try {
    const detail = await getPartRevision(revision.id)
    downloadBase64Part(
      detail.data,
      defaultDownloadName(detail.parts_id, detail.ptype, detail.filename),
      mimeTypeForPart(detail.ptype),
    )
  } catch (e) {
    localError.value = formatApiError(e)
  } finally {
    downloadingRevisionId.value = null
  }
}

async function onReplaceBinaryPart(part: PartInfo): Promise<void> {
  localError.value = null
  const file = await pickFile(acceptForPartType(part.ptype))
  if (!file) {
    return
  }
  replacingPartId.value = part.id
  try {
    const base64 = await readFileAsBase64(file)
    emit('update', part, part.ptype, base64, file.name)
  } finally {
    replacingPartId.value = null
  }
}

function partLabel(ptype: PartsType): string {
  return partTypeOptions.find((o) => o.value === ptype)?.label ?? ptype
}
</script>

<template>
  <section class="parts-panel">
    <p v-if="localError" class="status error">{{ localError }}</p>

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
          <p v-if="part.filename" class="binary-filename">{{ part.filename }}</p>
          <img
            class="part-image"
            :src="`data:image/${part.ptype};base64,${part.data}`"
            :alt="part.filename || `part-${part.id}`"
          />
          <div class="binary-actions">
            <button type="button" @click="onDownloadBinaryPart(part)">ダウンロード</button>
            <button
              type="button"
              :disabled="replacingPartId === part.id"
              @click="onReplaceBinaryPart(part)"
            >
              {{ replacingPartId === part.id ? '置き換え中…' : '置き換え' }}
            </button>
          </div>
          <div v-if="part.revisions.length > 0" class="revision-list">
            <p class="revision-title">過去の世代</p>
            <ul>
              <li v-for="rev in part.revisions" :key="rev.id" class="revision-row">
                <span class="revision-label">
                  #{{ rev.revision_number }} {{ rev.filename }}
                  <small>{{ rev.created_at }}</small>
                </span>
                <button
                  type="button"
                  :disabled="downloadingRevisionId === rev.id"
                  @click="onDownloadRevision(rev)"
                >
                  {{ downloadingRevisionId === rev.id ? '取得中…' : 'ダウンロード' }}
                </button>
              </li>
            </ul>
          </div>
        </template>
        <template v-else-if="part.ptype === 'url'">
          <a :href="part.data" target="_blank" rel="noopener noreferrer">{{ part.data }}</a>
        </template>
        <template v-else-if="part.ptype === 'binary'">
          <p v-if="part.filename" class="binary-filename">{{ part.filename }}</p>
          <p class="binary-hint">バイナリデータ（約 {{ formatByteSize(part.data.length) }}）</p>
          <div class="binary-actions">
            <button type="button" @click="onDownloadBinaryPart(part)">ダウンロード</button>
            <button
              type="button"
              :disabled="replacingPartId === part.id"
              @click="onReplaceBinaryPart(part)"
            >
              {{ replacingPartId === part.id ? '置き換え中…' : '置き換え' }}
            </button>
          </div>
          <div v-if="part.revisions.length > 0" class="revision-list">
            <p class="revision-title">過去の世代</p>
            <ul>
              <li v-for="rev in part.revisions" :key="rev.id" class="revision-row">
                <span class="revision-label">
                  #{{ rev.revision_number }} {{ rev.filename }}
                  <small>{{ rev.created_at }}</small>
                </span>
                <button
                  type="button"
                  :disabled="downloadingRevisionId === rev.id"
                  @click="onDownloadRevision(rev)"
                >
                  {{ downloadingRevisionId === rev.id ? '取得中…' : 'ダウンロード' }}
                </button>
              </li>
            </ul>
          </div>
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
                part.filename,
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
        <button type="button" @click="onPickBinaryFileForNew">ファイルを選択</button>
        <span v-if="newFilename">{{ newFilename }}（約 {{ formatByteSize(newData.length) }}）</span>
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
