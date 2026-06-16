/** パーツ種別（DB: note.parts_type） */
export type PartsType = 'jpeg' | 'png' | 'text' | 'tex' | 'md' | 'binary' | 'url' | 'action'

export interface ResultResponse {
  result: boolean
  reason: string | null
}

export interface ParentInfo {
  id: number | null
  name: string | null
}

export interface FolderItem {
  id: number
  dorder: number
  name: string
  is_del: boolean
}

export interface FileItem {
  id: number
  dorder: number
  title: string
  is_del: boolean
}

export interface ItemsListResponse {
  parent: ParentInfo
  folder: FolderItem[]
  file: FileItem[]
}

export interface BelongInfo {
  id: number
  name: string
}

export interface PartRevisionSummary {
  id: number
  revision_number: number
  filename: string
  ptype: PartsType
  created_at: string
}

export interface PartInfo {
  id: number
  dorder: number
  ptype: PartsType
  data: string
  filename: string
  is_del: boolean
  revisions: PartRevisionSummary[]
}

export interface PartRevisionGetResponse {
  id: number
  parts_id: number
  revision_number: number
  filename: string
  ptype: PartsType
  data: string
  created_at: string
}

export interface FileGetResponse {
  id: number
  belong: BelongInfo
  title: string
  parts: PartInfo[]
}

export interface MeResponse {
  user: {
    id: number
    username: string
  }
}

/** ツリー表示用（フロント側で A-1 を再帰／遅延取得して構築） */
export interface TreeFolderNode {
  id: number
  name: string
  dorder: number
  children: TreeFolderNode[]
  files: FileItem[]
  loaded: boolean
}
