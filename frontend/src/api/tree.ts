import { listItems } from './noteApi'
import type { FileItem, TreeFolderNode } from './types'

export function createEmptyTreeNode(
  id: number,
  name: string,
  dorder: number,
): TreeFolderNode {
  return {
    id,
    name,
    dorder,
    children: [],
    files: [],
    loaded: false,
  }
}

/** A-1 を使い、指定フォルダの子を読み込んでノードを更新する（遅延展開向け） */
export async function loadFolderChildren(node: TreeFolderNode): Promise<void> {
  const res = await listItems(node.id, false)
  node.children = res.folder
    .filter((f) => !f.is_del)
    .map((f) => createEmptyTreeNode(f.id, f.name, f.dorder))
  node.files = res.file.filter((f) => !f.is_del)
  node.loaded = true
}

/** ルート直下のフォルダ一覧を取得 */
export async function loadRootFolders(): Promise<TreeFolderNode[]> {
  const res = await listItems(null, false)
  return res.folder
    .filter((f) => !f.is_del)
    .map((f) => createEmptyTreeNode(f.id, f.name, f.dorder))
}

export function findFolderNode(
  nodes: TreeFolderNode[],
  folderId: number,
): TreeFolderNode | null {
  for (const node of nodes) {
    if (node.id === folderId) {
      return node
    }
    const found = findFolderNode(node.children, folderId)
    if (found) {
      return found
    }
  }
  return null
}

export function collectFilesUnder(node: TreeFolderNode): FileItem[] {
  return [...node.files, ...node.children.flatMap(collectFilesUnder)]
}

export interface FlatFolderEntry {
  id: number
  name: string
  depth: number
  parentId: number | null
}

/** ツリー上で読み込み済みのフォルダをフラット化（移動先選択用） */
export function flattenLoadedFolders(
  nodes: TreeFolderNode[],
  parentId: number | null = null,
  depth = 0,
): FlatFolderEntry[] {
  const result: FlatFolderEntry[] = []
  for (const node of nodes) {
    result.push({ id: node.id, name: node.name, depth, parentId })
    if (node.loaded) {
      result.push(...flattenLoadedFolders(node.children, node.id, depth + 1))
    }
  }
  return result
}

export function containsFolderId(node: TreeFolderNode, folderId: number): boolean {
  if (node.id === folderId) {
    return true
  }
  return node.children.some((child) => containsFolderId(child, folderId))
}

/** 移動禁止対象（自身と子孫）の ID 集合 */
export function collectBlockedFolderIds(
  roots: TreeFolderNode[],
  folderId: number,
): Set<number> {
  const node = findFolderNode(roots, folderId)
  if (!node) {
    return new Set([folderId])
  }
  return new Set(collectDescendantIds(node))
}

function collectDescendantIds(node: TreeFolderNode): number[] {
  const ids = [node.id]
  for (const child of node.children) {
    ids.push(...collectDescendantIds(child))
  }
  return ids
}
