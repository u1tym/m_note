<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  createFolder,
  createFile,
  renameFolder,
  renameFile,
  moveFile,
  moveFolder,
  deleteFolder,
  deleteFile,
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

const router = useRouter()
const roots = ref<TreeFolderNode[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const selectedFolderId = ref<number | null>(null)

const pickerOpen = ref(false)
const pickerTitle = ref('')
const pickerExcludeIds = ref<Set<number>>(new Set())
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
  pickerOpen.value = true
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
  pickerOpen.value = true
}

async function onPickerPick(newParentId: number): Promise<void> {
  const target = moveTarget.value
  pickerOpen.value = false
  moveTarget.value = null

  if (!target) {
    return
  }

  await runAction(async () => {
    if (target.kind === 'file') {
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
      await reloadNode(newParentId)
    }
  })
}

function onPickerCancel(): void {
  pickerOpen.value = false
  moveTarget.value = null
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
    <header class="page-header">
      <BackToMenuButton />
      <h1>メモ</h1>
    </header>

    <p v-if="loading" class="status">読み込み中…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <FolderTree
      v-else
      :roots="roots"
      :selected-folder-id="selectedFolderId"
      @expand="onExpand"
      @select-folder="onSelectFolder"
      @open-file="openFile"
      @create-root-folder="onCreateRootFolder"
      @create-child-folder="onCreateChildFolder"
      @rename-folder="onRenameFolder"
      @delete-folder="onDeleteFolder"
      @move-folder="onRequestMoveFolder"
      @create-file="onCreateFile"
      @rename-file="onRenameFile"
      @delete-file="onDeleteFile"
      @move-file="onRequestMoveFile"
    />

    <FolderPicker
      :open="pickerOpen"
      :title="pickerTitle"
      :folders="pickerFolders"
      :exclude-ids="pickerExcludeIds"
      @pick="onPickerPick"
      @cancel="onPickerCancel"
    />
  </div>
</template>
