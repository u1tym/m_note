import { postNote } from './noteClient'
import type {
  FileGetResponse,
  ItemsListResponse,
  PartRevisionGetResponse,
  PartsType,
  ResultResponse,
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
