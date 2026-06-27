<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

defineOptions({ name: 'HomeView' })

import {
  createFolder,
  createFile,
  renameFolder,
  renameFile,
  moveFile,
  moveFolder,
  deleteFolder,
  deleteFile,
  swapFolderOrder,
  swapFileOrder,
  getFile,
} from '../api/noteApi'
import {
  loadRootFolders,
  loadFolderChildren,
  flattenLoadedFolders,
  collectBlockedFolderIds,
  findFolderNode,
} from '../api/tree'
import type { TreeFolderNode } from '../api/types'
import { formatApiError } from '../api/errors'
import FolderTree from '../components/FolderTree.vue'
import FolderPicker from '../components/FolderPicker.vue'
import BackToMenuButton from '../components/BackToMenuButton.vue'
import MultiFilePrintDocument, {
  type PrintFilePayload,
} from '../components/MultiFilePrintDocument.vue'
import type { PdfSelectionItem } from '../utils/pdfExport'
import { waitUntil } from '../utils/waitUntil'

const router = useRouter()
const roots = ref<TreeFolderNode[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const selectedFolderId = ref<number | null>(null)
const editMode = ref(false)
const pdfExportMode = ref(false)
const pdfSelection = ref<PdfSelectionItem[]>([])
const printPayload = ref<PrintFilePayload[]>([])
const printReady = ref(false)
const printExportKey = ref(0)
const exportingPdf = ref(false)
const pdfError = ref<string | null>(null)
const pdfPageBreakBetweenFiles = ref(true)

const selectedPdfFileIds = computed(
  () => new Set(pdfSelection.value.map((item) => item.fileId)),
)

function toggleEditMode(): void {
  editMode.value = !editMode.value
  if (editMode.value) {
    pdfExportMode.value = false
    pdfSelection.value = []
    printPayload.value = []
  }
}

function togglePdfExportMode(): void {
  pdfExportMode.value = !pdfExportMode.value
  if (pdfExportMode.value) {
    editMode.value = false
    pdfError.value = null
  } else {
    pdfSelection.value = []
    printPayload.value = []
    printReady.value = false
    pdfError.value = null
    exportingPdf.value = false
    pdfPageBreakBetweenFiles.value = true
  }
}

function onTogglePdfFile(item: PdfSelectionItem): void {
  const index = pdfSelection.value.findIndex((entry) => entry.fileId === item.fileId)
  if (index >= 0) {
    pdfSelection.value = pdfSelection.value.filter((entry) => entry.fileId !== item.fileId)
    return
  }
  pdfSelection.value = [...pdfSelection.value, item]
}

function movePdfSelection(index: number, direction: -1 | 1): void {
  const target = index + direction
  if (target < 0 || target >= pdfSelection.value.length) {
    return
  }
  const next = [...pdfSelection.value]
  const [item] = next.splice(index, 1)
  next.splice(target, 0, item)
  pdfSelection.value = next
}

function removePdfSelection(fileId: number): void {
  pdfSelection.value = pdfSelection.value.filter((entry) => entry.fileId !== fileId)
}

async function onExportCombinedPdf(): Promise<void> {
  if (pdfSelection.value.length === 0 || exportingPdf.value) {
    return
  }
  exportingPdf.value = true
  printReady.value = false
  pdfError.value = null
  printPayload.value = []
  try {
    const loaded: PrintFilePayload[] = []
    for (const item of pdfSelection.value) {
      const data = await getFile(item.fileId, false)
      loaded.push({
        fileId: item.fileId,
        folderName: data.belong.name,
        fileTitle: data.title,
        parts: data.parts.filter((part) => !part.is_del),
      })
    }
    printExportKey.value += 1
    printPayload.value = loaded
    await nextTick()
    const ready = await waitUntil(() => printReady.value)
    if (!ready) {
      throw new Error('PDF出力の準備に失敗しました')
    }
    window.print()
  } catch (e) {
    pdfError.value = formatApiError(e)
    printPayload.value = []
    printReady.value = false
  } finally {
    exportingPdf.value = false
  }
}

const pickerOpen = ref(false)
const pickerTitle = ref('')
const pickerExcludeIds = ref<Set<number>>(new Set())
const pickerAllowRoot = ref(false)
const moveTarget = ref<
  | { kind: 'file'; fileId: number; oldParentId: number }
  | { kind: 'folder'; folderId: number; oldParentId: number | null }
  | null
>(null)

const pickerFolders = computed(() => flattenLoadedFolders(roots.value))

function findNode(nodes: TreeFolderNode[], id: number): TreeFolderNode | null {
  return findFolderNode(nodes, id)
}

async function reloadNode(folderId: number): Promise<void> {
  const node = findNode(roots.value, folderId)
  if (node) {
    node.loaded = false
    await loadFolderChildren(node)
  }
}

async function refreshRoots(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    roots.value = await loadRootFolders()
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

async function runAction(action: () => Promise<void>): Promise<void> {
  error.value = null
  try {
    await action()
  } catch (e) {
    error.value = formatApiError(e)
  }
}

async function onExpand(folderId: number): Promise<void> {
  const node = findNode(roots.value, folderId)
  if (!node || node.loaded) {
    return
  }
  await loadFolderChildren(node)
}

async function onCreateRootFolder(name: string): Promise<void> {
  await runAction(async () => {
    const res = await createFolder(null, name)
    if (!res.result) {
      throw new Error(res.reason ?? 'フォルダ作成に失敗しました')
    }
    await refreshRoots()
  })
}

async function onCreateChildFolder(parentId: number, name: string): Promise<void> {
  await runAction(async () => {
    const res = await createFolder(parentId, name)
    if (!res.result) {
      throw new Error(res.reason ?? 'フォルダ作成に失敗しました')
    }
    await reloadNode(parentId)
  })
}

async function onRenameFolder(folderId: number, name: string): Promise<void> {
  await runAction(async () => {
    const res = await renameFolder(folderId, name)
    if (!res.result) {
      throw new Error(res.reason ?? '名前変更に失敗しました')
    }
    await refreshRoots()
  })
}

async function onDeleteFolder(folderId: number, parentId: number | null): Promise<void> {
  if (!window.confirm('このフォルダを削除しますか？（論理削除）')) {
    return
  }
  await runAction(async () => {
    const res = await deleteFolder(folderId)
    if (!res.result) {
      throw new Error(res.reason ?? 'フォルダ削除に失敗しました')
    }
    if (parentId === null) {
      await refreshRoots()
    } else {
      await reloadNode(parentId)
    }
  })
}

function onRequestMoveFolder(folderId: number, parentId: number | null): void {
  moveTarget.value = { kind: 'folder', folderId, oldParentId: parentId }
  pickerTitle.value = 'フォルダの移動先'
  pickerExcludeIds.value = collectBlockedFolderIds(roots.value, folderId)
  pickerAllowRoot.value = true
  pickerOpen.value = true
}

async function onReorderFolder(
  parentId: number | null,
  folderId1: number,
  folderId2: number,
): Promise<void> {
  await runAction(async () => {
    const res = await swapFolderOrder(parentId, folderId1, folderId2)
    if (!res.result) {
      throw new Error(res.reason ?? 'フォルダの並び替えに失敗しました')
    }
    if (parentId === null) {
      await refreshRoots()
    } else {
      await reloadNode(parentId)
    }
  })
}

async function onCreateFile(folderId: number, title: string): Promise<void> {
  await runAction(async () => {
    const res = await createFile(folderId, title)
    if (!res.result) {
      throw new Error(res.reason ?? 'ファイル作成に失敗しました')
    }
    await reloadNode(folderId)
  })
}

async function onRenameFile(fileId: number, name: string, folderId: number): Promise<void> {
  await runAction(async () => {
    const res = await renameFile(fileId, name)
    if (!res.result) {
      throw new Error(res.reason ?? 'ファイル名変更に失敗しました')
    }
    await reloadNode(folderId)
  })
}

async function onDeleteFile(fileId: number, folderId: number): Promise<void> {
  if (!window.confirm('このファイルを削除しますか？（論理削除）')) {
    return
  }
  await runAction(async () => {
    const res = await deleteFile(fileId)
    if (!res.result) {
      throw new Error(res.reason ?? 'ファイル削除に失敗しました')
    }
    await reloadNode(folderId)
  })
}

function onRequestMoveFile(fileId: number, oldParentId: number): void {
  moveTarget.value = { kind: 'file', fileId, oldParentId }
  pickerTitle.value = 'ファイルの移動先'
  pickerExcludeIds.value = new Set()
  pickerAllowRoot.value = false
  pickerOpen.value = true
}

async function onReorderFile(
  folderId: number,
  fileId1: number,
  fileId2: number,
): Promise<void> {
  await runAction(async () => {
    const res = await swapFileOrder(folderId, fileId1, fileId2)
    if (!res.result) {
      throw new Error(res.reason ?? 'ファイルの並び替えに失敗しました')
    }
    await reloadNode(folderId)
  })
}

async function onPickerPick(newParentId: number | null): Promise<void> {
  const target = moveTarget.value
  pickerOpen.value = false
  moveTarget.value = null
  pickerAllowRoot.value = false

  if (!target) {
    return
  }

  await runAction(async () => {
    if (target.kind === 'file') {
      if (newParentId === null) {
        return
      }
      if (target.oldParentId === newParentId) {
        return
      }
      const res = await moveFile(target.fileId, target.oldParentId, newParentId)
      if (!res.result) {
        throw new Error(res.reason ?? 'ファイル移動に失敗しました')
      }
      await reloadNode(target.oldParentId)
      await reloadNode(newParentId)
    } else {
      if (target.oldParentId === newParentId) {
        return
      }
      const res = await moveFolder(target.folderId, target.oldParentId, newParentId)
      if (!res.result) {
        throw new Error(res.reason ?? 'フォルダ移動に失敗しました')
      }
      if (target.oldParentId === null) {
        await refreshRoots()
      } else {
        await reloadNode(target.oldParentId)
      }
      if (newParentId === null) {
        await refreshRoots()
      } else {
        await reloadNode(newParentId)
      }
    }
  })
}

function onPickerCancel(): void {
  pickerOpen.value = false
  moveTarget.value = null
  pickerAllowRoot.value = false
}

function onSelectFolder(folderId: number | null): void {
  selectedFolderId.value = folderId
}

function openFile(fileId: number): void {
  router.push({ name: 'file', params: { fileId } })
}

onMounted(() => {
  void refreshRoots()
})
</script>

<template>
  <div class="page">
    <div class="screen-only">
      <header class="page-header page-header--inline">
        <BackToMenuButton />
        <h1>Note</h1>
        <div v-if="!loading" class="page-header-actions">
          <button
            type="button"
            class="header-edit-btn"
            :aria-pressed="pdfExportMode"
            :disabled="editMode"
            @click="togglePdfExportMode"
          >
            {{ pdfExportMode ? 'PDF完了' : 'PDF出力' }}
          </button>
          <button
            type="button"
            class="header-edit-btn"
            :aria-pressed="editMode"
            :disabled="pdfExportMode"
            @click="toggleEditMode"
          >
            {{ editMode ? '完了' : '編集' }}
          </button>
        </div>
      </header>

      <p v-if="loading" class="status">読み込み中…</p>
      <p v-if="error" class="status error">{{ error }}</p>

      <template v-if="!loading">
        <p v-if="pdfExportMode" class="pdf-export-hint">
          ファイルをクリックして選択します。選択した順に PDF に連結されます。
        </p>

        <FolderTree
          :roots="roots"
          :selected-folder-id="selectedFolderId"
          :edit-mode="editMode"
          :pdf-export-mode="pdfExportMode"
          :selected-pdf-file-ids="selectedPdfFileIds"
          @expand="onExpand"
          @select-folder="onSelectFolder"
          @open-file="openFile"
          @toggle-pdf-file="onTogglePdfFile"
          @create-root-folder="onCreateRootFolder"
          @create-child-folder="onCreateChildFolder"
          @rename-folder="onRenameFolder"
          @delete-folder="onDeleteFolder"
          @move-folder="onRequestMoveFolder"
          @reorder-folder="onReorderFolder"
          @create-file="onCreateFile"
          @rename-file="onRenameFile"
          @delete-file="onDeleteFile"
          @move-file="onRequestMoveFile"
          @reorder-file="onReorderFile"
        />

        <section v-if="pdfExportMode" class="pdf-selection-panel">
          <p v-if="pdfError" class="status error pdf-selection-error">{{ pdfError }}</p>
          <h2 class="pdf-selection-title">出力するファイル（{{ pdfSelection.length }}件）</h2>
          <p v-if="pdfSelection.length === 0" class="empty-hint">
            一覧からファイルを選択してください。
          </p>
          <ol v-else class="pdf-selection-list">
            <li v-for="(item, index) in pdfSelection" :key="item.fileId" class="pdf-selection-row">
              <span class="pdf-selection-label">
                <span class="pdf-selection-order">{{ index + 1 }}.</span>
                <span class="pdf-selection-folder">{{ item.folderName }}</span>
                <span class="pdf-selection-name">{{ item.title }}</span>
              </span>
              <div class="pdf-selection-actions">
                <button
                  type="button"
                  class="reorder-btn"
                  :disabled="index === 0"
                  aria-label="上へ"
                  @click="movePdfSelection(index, -1)"
                >
                  ↑
                </button>
                <button
                  type="button"
                  class="reorder-btn"
                  :disabled="index === pdfSelection.length - 1"
                  aria-label="下へ"
                  @click="movePdfSelection(index, 1)"
                >
                  ↓
                </button>
                <button
                  type="button"
                  class="pdf-selection-remove"
                  @click="removePdfSelection(item.fileId)"
                >
                  除外
                </button>
              </div>
            </li>
          </ol>
          <label class="pdf-page-break-option">
            <input v-model="pdfPageBreakBetweenFiles" type="checkbox" />
            ファイルごとに改ページ
          </label>
          <button
            type="button"
            class="pdf-export-btn"
            :disabled="pdfSelection.length === 0 || exportingPdf"
            @click="onExportCombinedPdf"
          >
            {{ exportingPdf ? '準備中…' : 'PDFに出力' }}
          </button>
        </section>
      </template>

      <FolderPicker
        :open="pickerOpen"
        :title="pickerTitle"
        :folders="pickerFolders"
        :exclude-ids="pickerExcludeIds"
        :allow-root="pickerAllowRoot"
        @pick="onPickerPick"
        @cancel="onPickerCancel"
      />
    </div>

    <div v-if="printPayload.length > 0" class="print-only" aria-hidden="true">
      <MultiFilePrintDocument
        :key="printExportKey"
        :files="printPayload"
        :page-break-between-files="pdfPageBreakBetweenFiles"
        @ready="printReady = true"
      />
    </div>
  </div>
</template>
