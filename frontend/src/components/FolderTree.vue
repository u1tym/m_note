<script setup lang="ts">
import { computed, ref } from 'vue'

import type { FileItem, TreeFolderNode } from '../api/types'
import FolderTreeNode from './FolderTreeNode.vue'

const props = defineProps<{
  roots: TreeFolderNode[]
  selectedFolderId: number | null
  editMode: boolean
}>()

const emit = defineEmits<{
  expand: [folderId: number]
  selectFolder: [folderId: number | null]
  openFile: [fileId: number]
  createRootFolder: [name: string]
  createChildFolder: [parentId: number, name: string]
  renameFolder: [folderId: number, name: string]
  deleteFolder: [folderId: number, parentId: number | null]
  moveFolder: [folderId: number, parentId: number | null]
  reorderFolder: [parentId: number | null, folderId1: number, folderId2: number]
  createFile: [folderId: number, title: string]
  renameFile: [fileId: number, name: string, folderId: number]
  deleteFile: [fileId: number, folderId: number]
  moveFile: [fileId: number, oldParentId: number]
  reorderFile: [folderId: number, fileId1: number, fileId2: number]
}>()

const sortedRoots = computed(() => [...props.roots].sort((a, b) => a.dorder - b.dorder))

const expandedIds = ref<Set<number>>(new Set())

async function toggleExpand(folderId: number): Promise<void> {
  if (expandedIds.value.has(folderId)) {
    expandedIds.value.delete(folderId)
    return
  }
  expandedIds.value.add(folderId)
  emit('expand', folderId)
}

function promptName(label: string): string | null {
  const name = window.prompt(label)
  if (!name?.trim()) {
    return null
  }
  return name.trim()
}

function onCreateRoot(): void {
  const name = promptName('ルートに作るフォルダ名')
  if (name) {
    emit('createRootFolder', name)
  }
}

function onCreateChild(parentId: number): void {
  const name = promptName('フォルダ名')
  if (name) {
    emit('createChildFolder', parentId, name)
  }
}

function onRenameFolder(folderId: number, current: string): void {
  const name = promptName('新しいフォルダ名')
  if (name && name !== current) {
    emit('renameFolder', folderId, name)
  }
}

function onCreateFile(folderId: number): void {
  const title = promptName('ファイル名')
  if (title) {
    emit('createFile', folderId, title)
  }
}

function onRenameFile(file: FileItem, folderId: number): void {
  const title = promptName('新しいファイル名')
  if (title && title !== file.title) {
    emit('renameFile', file.id, title, folderId)
  }
}
</script>

<template>
  <section class="tree-panel">
    <div v-if="!editMode" class="tree-toolbar">
      <button type="button" class="tree-icon-btn" title="ルートフォルダを追加" @click="onCreateRoot">
        +📁
      </button>
    </div>

    <ul class="tree-root">
      <FolderTreeNode
        v-for="node in sortedRoots"
        :key="node.id"
        :node="node"
        :depth="0"
        :parent-id="null"
        :folder-siblings="sortedRoots"
        :expanded-ids="expandedIds"
        :selected-folder-id="selectedFolderId"
        :edit-mode="editMode"
        @toggle-expand="toggleExpand"
        @select-folder="(id) => emit('selectFolder', id)"
        @open-file="(id) => emit('openFile', id)"
        @create-child="onCreateChild"
        @rename-folder="onRenameFolder"
        @delete-folder="(id, pid) => emit('deleteFolder', id, pid)"
        @move-folder="(id, pid) => emit('moveFolder', id, pid)"
        @reorder-folder="(pid, id1, id2) => emit('reorderFolder', pid, id1, id2)"
        @create-file="onCreateFile"
        @rename-file="onRenameFile"
        @delete-file="(id, fid) => emit('deleteFile', id, fid)"
        @move-file="(id, fid) => emit('moveFile', id, fid)"
        @reorder-file="(fid, id1, id2) => emit('reorderFile', fid, id1, id2)"
      />
    </ul>

    <p v-if="roots.length === 0" class="empty-hint">
      フォルダがありません。ルートフォルダを作成してください。
    </p>
  </section>
</template>
