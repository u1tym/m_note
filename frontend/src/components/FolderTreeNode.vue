<script setup lang="ts">
import type { FileItem, TreeFolderNode } from '../api/types'
import FolderTreeNode from './FolderTreeNode.vue'

defineProps<{
  node: TreeFolderNode
  depth: number
  parentId: number | null
  expandedIds: Set<number>
  selectedFolderId: number | null
}>()

const emit = defineEmits<{
  toggleExpand: [folderId: number]
  selectFolder: [folderId: number]
  openFile: [fileId: number]
  createChild: [parentId: number]
  renameFolder: [folderId: number, current: string]
  deleteFolder: [folderId: number, parentId: number | null]
  moveFolder: [folderId: number, parentId: number | null]
  createFile: [folderId: number]
  renameFile: [file: FileItem, folderId: number]
  deleteFile: [fileId: number, folderId: number]
  moveFile: [fileId: number, folderId: number]
}>()

function isExpanded(folderId: number, expandedIds: Set<number>): boolean {
  return expandedIds.has(folderId)
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
        @click="emit('toggleExpand', node.id)"
      >
        {{ isExpanded(node.id, expandedIds) ? '▼' : '▶' }}
      </button>
      <button type="button" class="folder-name" @click="emit('selectFolder', node.id)">
        📁 {{ node.name }}
      </button>
      <div class="row-actions">
        <button type="button" title="子フォルダ追加" @click="emit('createChild', node.id)">+📁</button>
        <button type="button" title="ファイル追加" @click="emit('createFile', node.id)">+📄</button>
        <button type="button" title="名前変更" @click="emit('renameFolder', node.id, node.name)">✎</button>
        <button type="button" title="移動" @click="emit('moveFolder', node.id, parentId)">⇄</button>
        <button type="button" class="danger" title="削除" @click="emit('deleteFolder', node.id, parentId)">🗑</button>
      </div>
    </div>

    <ul v-if="isExpanded(node.id, expandedIds)" class="tree-children">
      <FolderTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :parent-id="node.id"
        :expanded-ids="expandedIds"
        :selected-folder-id="selectedFolderId"
        @toggle-expand="(id) => emit('toggleExpand', id)"
        @select-folder="(id) => emit('selectFolder', id)"
        @open-file="(id) => emit('openFile', id)"
        @create-child="(id) => emit('createChild', id)"
        @rename-folder="(id, name) => emit('renameFolder', id, name)"
        @delete-folder="(id, pid) => emit('deleteFolder', id, pid)"
        @move-folder="(id, pid) => emit('moveFolder', id, pid)"
        @create-file="(id) => emit('createFile', id)"
        @rename-file="(file, fid) => emit('renameFile', file, fid)"
        @delete-file="(id, fid) => emit('deleteFile', id, fid)"
        @move-file="(id, fid) => emit('moveFile', id, fid)"
      />

      <li
        v-for="file in node.files"
        :key="file.id"
        class="file-row"
        :style="{ paddingLeft: `${(depth + 1) * 12 + 28}px` }"
      >
        <button type="button" class="file-name" @click="emit('openFile', file.id)">
          📄 {{ file.title }}
        </button>
        <div class="row-actions">
          <button type="button" title="名前変更" @click="emit('renameFile', file, node.id)">✎</button>
          <button type="button" title="移動" @click="emit('moveFile', file.id, node.id)">⇄</button>
          <button type="button" class="danger" title="削除" @click="emit('deleteFile', file.id, node.id)">🗑</button>
        </div>
      </li>
    </ul>
  </li>
</template>
