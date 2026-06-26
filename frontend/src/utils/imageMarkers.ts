import type { ImageMarker } from '../api/types'

export function parseImageMarkers(raw: unknown): ImageMarker[] {
  if (!Array.isArray(raw)) {
    return []
  }
  const markers: ImageMarker[] = []
  for (const item of raw) {
    if (!item || typeof item !== 'object') {
      continue
    }
    const record = item as Record<string, unknown>
    const kind = record.kind
    if (kind !== 'house' && kind !== 'number') {
      continue
    }
    const id = typeof record.id === 'string' ? record.id : ''
    const x = typeof record.x === 'number' ? record.x : Number.NaN
    const y = typeof record.y === 'number' ? record.y : Number.NaN
    if (!id || Number.isNaN(x) || Number.isNaN(y)) {
      continue
    }
    const text = typeof record.text === 'string' ? record.text : ''
    if (kind === 'house') {
      markers.push({ id, kind: 'house', x, y, text })
      continue
    }
    const number = typeof record.number === 'number' ? record.number : Number.NaN
    if (Number.isNaN(number) || number < 1) {
      continue
    }
    markers.push({ id, kind: 'number', number, x, y, text })
  }
  return markers
}

export function newMarkerId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `m-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function nextMarkerNumber(markers: ImageMarker[]): number {
  const numbers = markers
    .filter((marker) => marker.kind === 'number' && marker.number !== undefined)
    .map((marker) => marker.number as number)
  return numbers.length > 0 ? Math.max(...numbers) + 1 : 1
}

export function markerDisplayLabel(marker: ImageMarker): string {
  return marker.kind === 'house' ? '⌂' : String(marker.number)
}

export function cloneMarkers(markers: ImageMarker[]): ImageMarker[] {
  return markers.map((marker) => ({ ...marker }))
}
