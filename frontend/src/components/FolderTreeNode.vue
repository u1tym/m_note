<script setup lang="ts">
import { computed } from 'vue'

import type { FileItem, TreeFolderNode } from '../api/types'
import FolderTreeNode from './FolderTreeNode.vue'

const props = defineProps<{
  node: TreeFolderNode
  depth: number
  parentId: number | null
  folderSiblings: TreeFolderNode[]
  expandedIds: Set<number>
  selectedFolderId: number | null
  editMode: boolean
}>()

const emit = defineEmits<{
  toggleExpand: [folderId: number]
  selectFolder: [folderId: number]
  openFile: [fileId: number]
  createChild: [parentId: number]
  renameFolder: [folderId: number, current: string]
  deleteFolder: [folderId: number, parentId: number | null]
  moveFolder: [folderId: number, parentId: number | null]
  reorderFolder: [parentId: number | null, folderId1: number, folderId2: number]
  createFile: [folderId: number]
  renameFile: [file: FileItem, folderId: number]
  deleteFile: [fileId: number, folderId: number]
  moveFile: [fileId: number, folderId: number]
  reorderFile: [folderId: number, fileId1: number, fileId2: number]
}>()

const sortedChildren = computed(() =>
  [...props.node.children].sort((a, b) => a.dorder - b.dorder),
)

const sortedFiles = computed(() => [...props.node.files].sort((a, b) => a.dorder - b.dorder))

function isExpanded(folderId: number, expandedIds: Set<number>): boolean {
  return expandedIds.has(folderId)
}

function folderIndex(): number {
  return props.folderSiblings.findIndex((f) => f.id === props.node.id)
}

function fileIndex(file: FileItem): number {
  return sortedFiles.value.findIndex((f) => f.id === file.id)
}

function onMoveFolder(direction: -1 | 1): void {
  const index = folderIndex()
  const target = props.folderSiblings[index + direction]
  if (!target) {
    return
  }
  emit('reorderFolder', props.parentId, props.node.id, target.id)
}

function onMoveFile(file: FileItem, direction: -1 | 1): void {
  const index = fileIndex(file)
  const target = sortedFiles.value[index + direction]
  if (!target) {
    return
  }
  emit('reorderFile', props.node.id, file.id, target.id)
}
</script>

<template>
  <li class="tree-node">
    <div
      class="folder-row"
      :class="{ selected: selectedFolderId === node.id }"
      :style="{ paddingLeft: `${depth * 12 + 8}px` }"
    >
      <button
        type="button"
        class="expand-btn"
        :aria-expanded="isExpanded(node.id, expandedIds)"
        :aria-label="isExpanded(node.id, expandedIds) ? 'フォルダを閉じる' : 'フォルダを開く'"
        @click="emit('toggleExpand', node.id)"
      >
        {{ isExpanded(node.id, expandedIds) ? '📂' : '📁' }}
      </button>
      <button type="button" class="folder-name" @click="emit('selectFolder', node.id)">
        {{ node.name }}
      </button>
      <div class="row-actions">
        <template v-if="!editMode">
          <button type="button" title="子フォルダ追加" @click="emit('createChild', node.id)">+📁</button>
          <button type="button" title="ファイル追加" @click="emit('createFile', node.id)">+📄</button>
        </template>
        <template v-else>
          <div class="tree-reorder">
            <button
              type="button"
              class="reorder-btn"
              :disabled="folderIndex() === 0"
              aria-label="上へ"
              @click="onMoveFolder(-1)"
            >
              ↑
            </button>
            <button
              type="button"
              class="reorder-btn"
              :disabled="folderIndex() === folderSiblings.length - 1"
              aria-label="下へ"
              @click="onMoveFolder(1)"
            >
              ↓
            </button>
          </div>
          <button type="button" title="名前変更" @click="emit('renameFolder', node.id, node.name)">✎</button>
          <button type="button" title="移動" @click="emit('moveFolder', node.id, parentId)">⇄</button>
          <button type="button" class="danger" title="削除" @click="emit('deleteFolder', node.id, parentId)">🗑</button>
        </template>
      </div>
    </div>

    <ul v-if="isExpanded(node.id, expandedIds)" class="tree-children">
      <FolderTreeNode
        v-for="child in sortedChildren"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :parent-id="node.id"
        :folder-siblings="sortedChildren"
        :expanded-ids="expandedIds"
        :selected-folder-id="selectedFolderId"
        :edit-mode="editMode"
        @toggle-expand="(id) => emit('toggleExpand', id)"
        @select-folder="(id) => emit('selectFolder', id)"
        @open-file="(id) => emit('openFile', id)"
        @create-child="(id) => emit('createChild', id)"
        @rename-folder="(id, name) => emit('renameFolder', id, name)"
        @delete-folder="(id, pid) => emit('deleteFolder', id, pid)"
        @move-folder="(id, pid) => emit('moveFolder', id, pid)"
        @reorder-folder="(pid, id1, id2) => emit('reorderFolder', pid, id1, id2)"
        @create-file="(id) => emit('createFile', id)"
        @rename-file="(file, fid) => emit('renameFile', file, fid)"
        @delete-file="(id, fid) => emit('deleteFile', id, fid)"
        @move-file="(id, fid) => emit('moveFile', id, fid)"
        @reorder-file="(fid, id1, id2) => emit('reorderFile', fid, id1, id2)"
      />

      <li
        v-for="file in sortedFiles"
        :key="file.id"
        class="file-row"
        :style="{ paddingLeft: `${(depth + 1) * 12 + 8}px` }"
      >
        <span class="tree-row-icon" aria-hidden="true">📄</span>
        <button type="button" class="file-name" @click="emit('openFile', file.id)">
          {{ file.title }}
        </button>
        <div v-if="editMode" class="row-actions">
          <div class="tree-reorder">
            <button
              type="button"
              class="reorder-btn"
              :disabled="fileIndex(file) === 0"
              aria-label="上へ"
              @click="onMoveFile(file, -1)"
            >
              ↑
            </button>
            <button
              type="button"
              class="reorder-btn"
              :disabled="fileIndex(file) === sortedFiles.length - 1"
              aria-label="下へ"
              @click="onMoveFile(file, 1)"
            >
              ↓
            </button>
          </div>
          <button type="button" title="名前変更" @click="emit('renameFile', file, node.id)">✎</button>
          <button type="button" title="移動" @click="emit('moveFile', file.id, node.id)">⇄</button>
          <button type="button" class="danger" title="削除" @click="emit('deleteFile', file.id, node.id)">🗑</button>
        </div>
      </li>
    </ul>
  </li>
</template>
