/** パーツ種別（DB: note.parts_type） */
export type PartsType =
  | 'jpeg'
  | 'png'
  | 'text'
  | 'tex'
  | 'md'
  | 'binary'
  | 'url'
  | 'action'
  | 'table'
  | 'checklist'


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

export type ImageMarkerKind = 'house' | 'number'

export interface ImageMarker {
  id: string
  kind: ImageMarkerKind
  x: number
  y: number
  text: string
  number?: number
}

export interface PartInfo {
  id: number
  dorder: number
  ptype: PartsType
  data: string
  filename: string
  title: string
  markers: ImageMarker[]
  image_scale: number
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

export interface TableCellItem {
  x: number
  y: number
  cell_type: string
  input_value: string
  display_format: string
  display_value: string
  text_align: string
}

export interface TableColWidthItem {
  x: number
  width_px: number
}

export interface TableGetResponse {
  table_id: number
  title: string
  row_count: number
  col_count: number
  col_widths: TableColWidthItem[]
  cells: TableCellItem[]
}

export interface TableMutationResponse {
  table_id: number
  title: string
  row_count: number
  col_count: number
  col_widths: TableColWidthItem[]
  cells: TableCellItem[]
}

export interface ChecklistItemItem {
  id: number
  title: string
  is_checked: boolean
  dorder: number
}

export interface ChecklistCategoryItem {
  id: number
  name: string
  is_unnamed: boolean
  dorder: number
  items: ChecklistItemItem[]
}

export interface ChecklistGetResponse {
  checklist_id: number
  title: string
  categories: ChecklistCategoryItem[]
}

export interface ChecklistMutationResponse {
  checklist_id: number
  title: string
  categories: ChecklistCategoryItem[]
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
