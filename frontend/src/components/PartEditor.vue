<script setup lang="ts">
import { computed, ref, watch } from 'vue'

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
import {
  emptyActionPlan,
  parseActionPlan,
  serializeActionPlan,
  validateActionPlan,
  type ActionPlanData,
} from '../utils/actionPlan'
import ActionPlanEditor from './ActionPlanEditor.vue'
import ActionPlanView from './ActionPlanView.vue'
import MarkdownPreview from './MarkdownPreview.vue'
import TexPreview from './TexPreview.vue'

const props = defineProps<{
  parts: PartInfo[]
}>()

const emit = defineEmits<{
  add: [type: PartsType, data: string, filename: string]
  update: [part: PartInfo, type: PartsType, data: string, filename: string]
  delete: [partsId: number]
  reorder: [partsId1: number, partsId2: number]
}>()

const newType = ref<PartsType>('text')
const newData = ref('')
const newFilename = ref('')
const replacingPartId = ref<number | null>(null)
const downloadingRevisionId = ref<number | null>(null)
const localError = ref<string | null>(null)

const activePartId = ref<number | null>(null)
const sheetMode = ref<'actions' | 'edit'>('actions')
const editData = ref('')
const editFilename = ref('')
const editActionPlan = ref<ActionPlanData>(emptyActionPlan())
const newActionPlan = ref<ActionPlanData>(emptyActionPlan())
const saving = ref(false)

const partTypeOptions: { value: PartsType; label: string }[] = [
  { value: 'text', label: 'テキスト' },
  { value: 'md', label: 'Markdown' },
  { value: 'tex', label: 'TeX' },
  { value: 'url', label: 'URL' },
  { value: 'action', label: '行動予定' },
  { value: 'jpeg', label: 'JPEG' },
  { value: 'png', label: 'PNG' },
  { value: 'binary', label: 'バイナリ' },
]

const sortedParts = computed(() => [...props.parts].sort((a, b) => a.dorder - b.dorder))

const activePart = computed(() =>
  sortedParts.value.find((p) => p.id === activePartId.value) ?? null,
)

function isBinaryType(type: PartsType): boolean {
  return type === 'jpeg' || type === 'png' || type === 'binary'
}

function isActionType(type: PartsType): boolean {
  return type === 'action'
}

function hasPreview(type: PartsType): boolean {
  return type === 'md' || type === 'tex'
}

function partLabel(ptype: PartsType): string {
  return partTypeOptions.find((o) => o.value === ptype)?.label ?? ptype
}

function openPart(part: PartInfo): void {
  activePartId.value = part.id
  sheetMode.value = 'actions'
  localError.value = null
}

function closeSheet(): void {
  activePartId.value = null
  sheetMode.value = 'actions'
  editData.value = ''
  editFilename.value = ''
  editActionPlan.value = emptyActionPlan()
}

function startEdit(): void {
  const part = activePart.value
  if (!part) {
    return
  }
  if (isActionType(part.ptype)) {
    editActionPlan.value = parseActionPlan(part.data) ?? emptyActionPlan()
  } else {
    editData.value = part.data
  }
  editFilename.value = part.filename
  sheetMode.value = 'edit'
  localError.value = null
}

watch(activePartId, (id) => {
  if (id === null) {
    sheetMode.value = 'actions'
    editData.value = ''
    editFilename.value = ''
    editActionPlan.value = emptyActionPlan()
  }
})

watch(newType, (type) => {
  if (type === 'action') {
    newActionPlan.value = emptyActionPlan()
    newData.value = ''
  }
})

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
  if (isActionType(newType.value)) {
    const err = validateActionPlan(newActionPlan.value)
    if (err) {
      localError.value = err
      return
    }
    emit('add', 'action', serializeActionPlan(newActionPlan.value), '')
    newActionPlan.value = emptyActionPlan()
    return
  }
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
  closeSheet()
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

async function onReplaceBinaryInEdit(): Promise<void> {
  const part = activePart.value
  if (!part) {
    return
  }
  localError.value = null
  const file = await pickFile(acceptForPartType(part.ptype))
  if (!file) {
    return
  }
  replacingPartId.value = part.id
  try {
    editFilename.value = file.name
    editData.value = await readFileAsBase64(file)
  } finally {
    replacingPartId.value = null
  }
}

async function onSaveEdit(): Promise<void> {
  const part = activePart.value
  if (!part) {
    return
  }
  localError.value = null
  if (isActionType(part.ptype)) {
    const err = validateActionPlan(editActionPlan.value)
    if (err) {
      localError.value = err
      return
    }
    saving.value = true
    try {
      emit('update', part, part.ptype, serializeActionPlan(editActionPlan.value), '')
      closeSheet()
    } finally {
      saving.value = false
    }
    return
  }
  if (isBinaryType(part.ptype) && !editData.value) {
    localError.value = 'ファイルが必要です'
    return
  }
  if (isBinaryType(part.ptype) && !editFilename.value.trim()) {
    localError.value = 'ファイル名が必要です'
    return
  }
  saving.value = true
  try {
    emit('update', part, part.ptype, editData.value, editFilename.value.trim())
    closeSheet()
  } finally {
    saving.value = false
  }
}

function onMovePart(part: PartInfo, direction: -1 | 1): void {
  const index = sortedParts.value.findIndex((p) => p.id === part.id)
  const target = sortedParts.value[index + direction]
  if (!target) {
    return
  }
  emit('reorder', part.id, target.id)
}

function partIndex(part: PartInfo): number {
  return sortedParts.value.findIndex((p) => p.id === part.id)
}
</script>

<template>
  <section class="parts-panel">
    <p v-if="localError" class="status error">{{ localError }}</p>

    <ul class="parts-list">
      <li v-for="part in sortedParts" :key="part.id" class="part-card">
        <div class="part-reorder">
          <button
            type="button"
            class="reorder-btn"
            :disabled="partIndex(part) === 0"
            aria-label="上へ"
            @click.stop="onMovePart(part, -1)"
          >
            ↑
          </button>
          <button
            type="button"
            class="reorder-btn"
            :disabled="partIndex(part) === sortedParts.length - 1"
            aria-label="下へ"
            @click.stop="onMovePart(part, 1)"
          >
            ↓
          </button>
        </div>

        <button type="button" class="part-view" @click="openPart(part)">
            <span class="part-type">{{ partLabel(part.ptype) }}</span>

            <template v-if="part.ptype === 'jpeg' || part.ptype === 'png'">
              <img
                class="part-image"
                :src="`data:image/${part.ptype};base64,${part.data}`"
                :alt="part.filename || `part-${part.id}`"
              />
            </template>
            <template v-else-if="part.ptype === 'binary'">
              <span class="part-binary-name">{{ part.filename || '（名前なし）' }}</span>
            </template>
            <template v-else-if="part.ptype === 'url'">
              <span class="part-url">{{ part.data }}</span>
            </template>
            <template v-else-if="part.ptype === 'action'">
              <ActionPlanView :data="part.data" />
            </template>
            <template v-else-if="part.ptype === 'md'">
              <MarkdownPreview :source="part.data" />
            </template>
            <template v-else-if="part.ptype === 'tex'">
              <TexPreview :source="part.data" />
            </template>
            <template v-else>
              <pre class="part-text-view">{{ part.data }}</pre>
            </template>
        </button>
      </li>
    </ul>

    <div
      v-if="activePart"
      class="picker-overlay"
      role="dialog"
      aria-modal="true"
      @click.self="closeSheet"
    >
      <div class="picker-dialog part-sheet">
        <header class="part-sheet-header">
          <h2>{{ partLabel(activePart.ptype) }}</h2>
          <button type="button" class="sheet-close" @click="closeSheet">閉じる</button>
        </header>

        <template v-if="sheetMode === 'actions'">
          <div class="part-sheet-preview">
            <template v-if="activePart.ptype === 'jpeg' || activePart.ptype === 'png'">
              <p v-if="activePart.filename" class="binary-filename">{{ activePart.filename }}</p>
              <img
                class="part-image"
                :src="`data:image/${activePart.ptype};base64,${activePart.data}`"
                :alt="activePart.filename || `part-${activePart.id}`"
              />
            </template>
            <template v-else-if="activePart.ptype === 'binary'">
              <p class="part-binary-name">{{ activePart.filename || '（名前なし）' }}</p>
              <p class="binary-hint">約 {{ formatByteSize(activePart.data.length) }}</p>
            </template>
            <template v-else-if="activePart.ptype === 'url'">
              <a
                :href="activePart.data"
                target="_blank"
                rel="noopener noreferrer"
                class="part-url-link"
              >
                {{ activePart.data }}
              </a>
            </template>
            <template v-else-if="activePart.ptype === 'action'">
              <ActionPlanView :data="activePart.data" />
            </template>
            <template v-else-if="activePart.ptype === 'md'">
              <MarkdownPreview :source="activePart.data" />
            </template>
            <template v-else-if="activePart.ptype === 'tex'">
              <TexPreview :source="activePart.data" />
            </template>
            <template v-else>
              <pre class="part-text-view">{{ activePart.data }}</pre>
            </template>
          </div>

          <div class="part-sheet-actions">
            <button type="button" class="primary" @click="startEdit">編集</button>
            <button
              v-if="isBinaryType(activePart.ptype)"
              type="button"
              @click="onDownloadBinaryPart(activePart)"
            >
              ダウンロード
            </button>
            <button type="button" class="danger" @click="onDeletePart(activePart.id)">削除</button>
          </div>

          <div
            v-if="isBinaryType(activePart.ptype) && activePart.revisions.length > 0"
            class="revision-list"
          >
            <p class="revision-title">過去の世代</p>
            <ul>
              <li v-for="rev in activePart.revisions" :key="rev.id" class="revision-row">
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
          <div class="part-edit-form">
            <template v-if="isActionType(activePart.ptype)">
              <ActionPlanEditor v-model="editActionPlan" />
            </template>
            <template v-else-if="isBinaryType(activePart.ptype)">
              <p v-if="editFilename" class="binary-filename">{{ editFilename }}</p>
              <p v-if="editData" class="binary-hint">約 {{ formatByteSize(editData.length) }}</p>
              <button
                type="button"
                :disabled="replacingPartId === activePart.id"
                @click="onReplaceBinaryInEdit"
              >
                {{ replacingPartId === activePart.id ? '読み込み中…' : 'ファイルを選択' }}
              </button>
            </template>
            <template v-else>
              <textarea
                v-model="editData"
                class="part-text"
                rows="8"
                :placeholder="activePart.ptype === 'url' ? 'https://...' : '内容を入力'"
              />
              <div v-if="hasPreview(activePart.ptype) && editData" class="part-preview">
                <p class="preview-label">プレビュー</p>
                <MarkdownPreview v-if="activePart.ptype === 'md'" :source="editData" />
                <TexPreview v-else-if="activePart.ptype === 'tex'" :source="editData" />
              </div>
            </template>
          </div>

          <div class="part-sheet-actions">
            <button type="button" class="primary" :disabled="saving" @click="onSaveEdit">
              {{ saving ? '保存中…' : '保存' }}
            </button>
            <button type="button" @click="sheetMode = 'actions'">キャンセル</button>
          </div>
        </template>
      </div>
    </div>

    <div class="add-part">
      <h2>パーツを追加</h2>
      <select v-model="newType">
        <option v-for="opt in partTypeOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <ActionPlanEditor v-if="isActionType(newType)" v-model="newActionPlan" />
      <textarea
        v-else-if="!isBinaryType(newType)"
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
