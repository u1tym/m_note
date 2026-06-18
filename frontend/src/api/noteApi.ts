import { postNote } from './noteClient'
import type {
  FileGetResponse,
  ItemsListResponse,
  PartRevisionGetResponse,
  PartsType,
  ResultResponse,
  TableGetResponse,
  TableMutationResponse,
} from './types'

export async function listItems(
  folderId: number | null,
  includeDeleted = false,
): Promise<ItemsListResponse> {
  return postNote<ItemsListResponse>('/items/list', {
    folder_id: folderId,
    include_deleted: includeDeleted,
  })
}

export async function getFile(
  fileId: number,
  includeDeleted = false,
): Promise<FileGetResponse> {
  return postNote<FileGetResponse>('/files/get', {
    file_id: fileId,
    include_deleted: includeDeleted,
  })
}

export async function createFolder(
  parentId: number | null,
  name: string,
): Promise<ResultResponse> {
  return postNote<ResultResponse>('/folders/create', {
    parent_id: parentId,
    name,
  })
}

export async function renameFolder(folderId: number, name: string): Promise<ResultResponse> {
  return postNote<ResultResponse>('/folders/rename', { folder_id: folderId, name })
}

export async function moveFolder(
  folderId: number,
  oldParentId: number | null,
  newParentId: number | null,
): Promise<ResultResponse> {
  return postNote<ResultResponse>('/folders/move', {
    folder_id: folderId,
    old_parent_id: oldParentId,
    new_parent_id: newParentId,
  })
}

export async function deleteFolder(folderId: number): Promise<ResultResponse> {
  return postNote<ResultResponse>('/folders/delete', { folder_id: folderId })
}

export async function swapFolderOrder(
  parentId: number | null,
  folderId1: number,
  folderId2: number,
): Promise<ResultResponse> {
  return postNote<ResultResponse>('/folders/swap-order', {
    parent_id: parentId,
    folder_id_1: folderId1,
    folder_id_2: folderId2,
  })
}

export async function createFile(folderId: number, title: string): Promise<ResultResponse> {
  return postNote<ResultResponse>('/files/create', { folder_id: folderId, title })
}

export async function renameFile(fileId: number, name: string): Promise<ResultResponse> {
  return postNote<ResultResponse>('/files/rename', { file_id: fileId, name })
}

export async function moveFile(
  fileId: number,
  oldParentId: number,
  newParentId: number,
): Promise<ResultResponse> {
  return postNote<ResultResponse>('/files/move', {
    file_id: fileId,
    old_parent_id: oldParentId,
    new_parent_id: newParentId,
  })
}

export async function deleteFile(fileId: number): Promise<ResultResponse> {
  return postNote<ResultResponse>('/files/delete', { file_id: fileId })
}

export async function swapFileOrder(
  folderId: number,
  fileId1: number,
  fileId2: number,
): Promise<ResultResponse> {
  return postNote<ResultResponse>('/files/swap-order', {
    parent_id: folderId,
    file_id_1: fileId1,
    file_id_2: fileId2,
  })
}

export async function createPart(
  fileId: number,
  type: PartsType,
  data: string,
  filename = '',
): Promise<ResultResponse> {
  return postNote<ResultResponse>('/parts/create', {
    file_id: fileId,
    type,
    data,
    filename,
  })
}

export async function updatePart(
  partsId: number,
  type: PartsType,
  data: string,
  filename?: string,
): Promise<ResultResponse> {
  return postNote<ResultResponse>('/parts/update', {
    parts_id: partsId,
    type,
    data,
    ...(filename !== undefined ? { filename } : {}),
  })
}

export async function getPartRevision(revisionId: number): Promise<PartRevisionGetResponse> {
  return postNote<PartRevisionGetResponse>('/parts/revision/get', {
    revision_id: revisionId,
  })
}

export async function deletePart(partsId: number): Promise<ResultResponse> {
  return postNote<ResultResponse>('/parts/delete', { parts_id: partsId })
}

export async function swapPartOrder(
  fileId: number,
  partsId1: number,
  partsId2: number,
): Promise<ResultResponse> {
  return postNote<ResultResponse>('/parts/swap-order', {
    file_id: fileId,
    parts_id_1: partsId1,
    parts_id_2: partsId2,
  })
}

export async function getTable(tableId: number): Promise<TableGetResponse> {
  return postNote<TableGetResponse>('/table/get', { table_id: tableId })
}

export async function updateTableTitle(
  tableId: number,
  title: string,
): Promise<TableMutationResponse> {
  return postNote<TableMutationResponse>('/table/title/update', {
    table_id: tableId,
    title,
  })
}

export async function updateTableColWidth(params: {
  tableId: number
  x: number
  widthPx: number | null
}): Promise<TableMutationResponse> {
  return postNote<TableMutationResponse>('/table/col-width/update', {
    table_id: params.tableId,
    x: params.x,
    width_px: params.widthPx,
  })
}

export async function updateTableCell(params: {
  tableId: number
  x: number
  y: number
  cellType?: string
  inputValue?: string
  displayFormat?: string
  textAlign?: string
}): Promise<TableMutationResponse> {
  return postNote<TableMutationResponse>('/table/cells/update', {
    table_id: params.tableId,
    x: params.x,
    y: params.y,
    cell_type: params.cellType ?? null,
    input_value: params.inputValue ?? null,
    display_format: params.displayFormat ?? null,
    text_align: params.textAlign ?? null,
  })
}

export async function pasteTableCell(params: {
  tableId: number
  x: number
  y: number
  sourceInputValue: string
  sourceCellType: string
  sourceDisplayFormat: string
  sourceTextAlign?: string
  offsetX: number
  offsetY: number
}): Promise<TableMutationResponse> {
  return postNote<TableMutationResponse>('/table/cells/paste', {
    table_id: params.tableId,
    x: params.x,
    y: params.y,
    source_input_value: params.sourceInputValue,
    source_cell_type: params.sourceCellType,
    source_display_format: params.sourceDisplayFormat,
    source_text_align: params.sourceTextAlign ?? '左寄せ',
    offset_x: params.offsetX,
    offset_y: params.offsetY,
  })
}

export async function insertTableRow(
  tableId: number,
  atRow: number,
): Promise<TableMutationResponse> {
  return postNote<TableMutationResponse>('/table/rows/insert', {
    table_id: tableId,
    at_row: atRow,
  })
}

export async function deleteTableRow(
  tableId: number,
  atRow: number,
): Promise<TableMutationResponse> {
  return postNote<TableMutationResponse>('/table/rows/delete', {
    table_id: tableId,
    at_row: atRow,
  })
}

export async function insertTableCol(
  tableId: number,
  atCol: number,
): Promise<TableMutationResponse> {
  return postNote<TableMutationResponse>('/table/cols/insert', {
    table_id: tableId,
    at_col: atCol,
  })
}

export async function deleteTableCol(
  tableId: number,
  atCol: number,
): Promise<TableMutationResponse> {
  return postNote<TableMutationResponse>('/table/cols/delete', {
    table_id: tableId,
    at_col: atCol,
  })
}
