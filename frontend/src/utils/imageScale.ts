export const DEFAULT_IMAGE_SCALE = 1
export const MIN_IMAGE_SCALE = 0.25
export const MAX_IMAGE_SCALE = 4

export function clampImageScale(scale: number): number {
  if (!Number.isFinite(scale)) {
    return DEFAULT_IMAGE_SCALE
  }
  return Math.min(MAX_IMAGE_SCALE, Math.max(MIN_IMAGE_SCALE, scale))
}

export function scaleToPercent(scale: number): number {
  return Math.round(clampImageScale(scale) * 100)
}

export function percentToScale(percent: number): number {
  return clampImageScale(percent / 100)
}

export function imageScaleStyle(scale: number): { width: string } {
  const clamped = clampImageScale(scale)
  return { width: `${Math.round(clamped * 100)}%` }
}

export function markerPinPosition(
  marker: { x: number; y: number },
  scale: number,
): { left: string; top: string } {
  const clamped = clampImageScale(scale)
  // 横: キャンバス幅は 100% 基準のため倍率を掛ける
  // 縦: キャンバス高さはすでに倍率込みのため y はそのまま
  return {
    left: `${marker.x * clamped * 100}%`,
    top: `${marker.y * 100}%`,
  }
}

export function pointerToMarkerPosition(
  clientX: number,
  clientY: number,
  rect: DOMRect,
  scale: number,
): { x: number; y: number } {
  const clamped = clampImageScale(scale)
  if (rect.width === 0 || rect.height === 0 || clamped === 0) {
    return { x: 0, y: 0 }
  }
  return {
    x: Math.min(1, Math.max(0, (clientX - rect.left) / rect.width / clamped)),
    y: Math.min(1, Math.max(0, (clientY - rect.top) / rect.height)),
  }
}

export function scaledCanvasHeightPx(
  canvasWidthPx: number,
  imageAspect: number,
  scale: number,
): number {
  if (canvasWidthPx <= 0 || imageAspect <= 0) {
    return 0
  }
  return canvasWidthPx * imageAspect * clampImageScale(scale)
}
