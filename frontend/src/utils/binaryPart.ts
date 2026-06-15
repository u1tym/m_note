import type { PartsType } from '../api/types'

/** File を Base64 文字列に変換（API の data 形式） */
export async function readFileAsBase64(file: File): Promise<string> {
  const buffer = await file.arrayBuffer()
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]!)
  }
  return btoa(binary)
}

export function base64ToUint8Array(base64: string): Uint8Array {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

export function defaultDownloadName(partId: number, ptype: PartsType, filename?: string): string {
  if (filename?.trim()) {
    return filename.trim()
  }
  if (ptype === 'jpeg') {
    return `part-${partId}.jpg`
  }
  if (ptype === 'png') {
    return `part-${partId}.png`
  }
  return `part-${partId}.bin`
}

export function mimeTypeForPart(ptype: PartsType): string {
  if (ptype === 'jpeg') {
    return 'image/jpeg'
  }
  if (ptype === 'png') {
    return 'image/png'
  }
  return 'application/octet-stream'
}

/** Base64 データをローカルファイルとしてダウンロード */
export function downloadBase64Part(
  base64: string,
  filename: string,
  mimeType = 'application/octet-stream',
): void {
  const bytes = base64ToUint8Array(base64)
  const blob = new Blob([bytes], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export function pickFile(accept: string): Promise<File | null> {
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = accept
    input.onchange = () => {
      resolve(input.files?.[0] ?? null)
    }
    input.click()
  })
}

export function acceptForPartType(ptype: PartsType): string {
  if (ptype === 'jpeg') {
    return 'image/jpeg'
  }
  if (ptype === 'png') {
    return 'image/png'
  }
  return '*/*'
}

export function formatByteSize(base64Length: number): string {
  const bytes = Math.floor((base64Length * 3) / 4)
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
