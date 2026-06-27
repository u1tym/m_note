<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

import type { ImageMarker, ImageMarkerKind } from '../api/types'
import {
  clampImageScale,
  markerPinPosition,
  pointerToMarkerPosition,
  scaledCanvasHeightPx,
} from '../utils/imageScale'
import {
  markerDisplayLabel,
  newMarkerId,
  nextMarkerNumber,
} from '../utils/imageMarkers'

const props = withDefaults(
  defineProps<{
    ptype: 'jpeg' | 'png'
    data: string
    title?: string
    filename?: string
    showFilename?: boolean
    markers: ImageMarker[]
    imageScale?: number
    editable?: boolean
  }>(),
  {
    title: '',
    filename: '',
    showFilename: false,
    imageScale: 1,
    editable: false,
  },
)

const emit = defineEmits<{
  'update:markers': [markers: ImageMarker[]]
}>()

const placementKind = ref<ImageMarkerKind>('house')
const selectedId = ref<string | null>(null)
const canvasRef = ref<HTMLElement | null>(null)
const canvasWidthPx = ref(0)
const imageAspect = ref(0)

const imageSrc = computed(() => `data:image/${props.ptype};base64,${props.data}`)
const imageAlt = computed(
  () => props.title || props.filename || 'image part',
)
const clampedScale = computed(() => clampImageScale(props.imageScale))

const canvasStyle = computed(() => {
  const height = scaledCanvasHeightPx(canvasWidthPx.value, imageAspect.value, clampedScale.value)
  return {
    '--image-scale': String(clampedScale.value),
    ...(height > 0 ? { height: `${height}px` } : {}),
  }
})

const frameStyle = computed(() => ({
  width: `${Math.round(clampedScale.value * 100)}%`,
  height: '100%',
}))

function markerPinStyle(marker: ImageMarker): { left: string; top: string } {
  return markerPinPosition(marker, clampedScale.value)
}

function measureCanvas(): void {
  canvasWidthPx.value = canvasRef.value?.clientWidth ?? 0
}

function onImgLoad(event: Event): void {
  const img = event.target as HTMLImageElement
  if (img.naturalWidth > 0) {
    imageAspect.value = img.naturalHeight / img.naturalWidth
  }
  measureCanvas()
}

function onImageClick(event: MouseEvent): void {
  if (!props.editable || !canvasRef.value) {
    return
  }
  const rect = canvasRef.value.getBoundingClientRect()
  const { x, y } = pointerToMarkerPosition(
    event.clientX,
    event.clientY,
    rect,
    clampedScale.value,
  )
  addMarker(x, y)
}

function addMarker(x: number, y: number): void {
  const marker: ImageMarker =
    placementKind.value === 'house'
      ? { id: newMarkerId(), kind: 'house', x, y, text: '' }
      : {
          id: newMarkerId(),
          kind: 'number',
          number: nextMarkerNumber(props.markers),
          x,
          y,
          text: '',
        }
  emit('update:markers', [...props.markers, marker])
  selectedId.value = marker.id
}

function removeMarker(id: string): void {
  emit(
    'update:markers',
    props.markers.filter((marker) => marker.id !== id),
  )
  if (selectedId.value === id) {
    selectedId.value = null
  }
}

function updateMarkerText(id: string, text: string): void {
  emit(
    'update:markers',
    props.markers.map((marker) => (marker.id === id ? { ...marker, text } : marker)),
  )
}

function onMarkerPinClick(id: string, event: Event): void {
  event.stopPropagation()
  if (props.editable) {
    selectedId.value = id
  }
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  measureCanvas()
  if (canvasRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      measureCanvas()
    })
    resizeObserver.observe(canvasRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})

watch(
  () => [props.data, props.imageScale] as const,
  async () => {
    await nextTick()
    measureCanvas()
  },
)
</script>

<template>
  <div class="image-part">
    <p v-if="title" class="table-title">{{ title }}</p>
    <p v-if="showFilename && filename" class="binary-filename">{{ filename }}</p>

    <div v-if="editable" class="image-marker-toolbar">
      <span class="image-marker-toolbar-label">配置するマーカー</span>
      <div class="image-marker-kind-btns">
        <button
          type="button"
          class="image-marker-kind-btn"
          :class="{ 'image-marker-kind-btn--active': placementKind === 'house' }"
          @click="placementKind = 'house'"
        >
          ⌂ 家
        </button>
        <button
          type="button"
          class="image-marker-kind-btn"
          :class="{ 'image-marker-kind-btn--active': placementKind === 'number' }"
          @click="placementKind = 'number'"
        >
          番号
        </button>
      </div>
      <p class="image-marker-hint">画像をクリックしてマーカーを配置します</p>
    </div>

    <div ref="canvasRef" class="image-part-canvas" :style="canvasStyle">
      <div class="image-part-frame" :style="frameStyle">
        <img
          class="part-image"
          :class="{ 'part-image--placeable': editable }"
          :src="imageSrc"
          :alt="imageAlt"
          @load="onImgLoad"
          @click="onImageClick"
        />
      </div>
      <button
        v-for="marker in markers"
        :key="marker.id"
        type="button"
        class="image-marker-pin"
        :class="{
          'image-marker-pin--house': marker.kind === 'house',
          'image-marker-pin--number': marker.kind === 'number',
          'image-marker-pin--selected': editable && selectedId === marker.id,
        }"
        :style="markerPinStyle(marker)"
        :aria-label="marker.text || markerDisplayLabel(marker)"
        @click="onMarkerPinClick(marker.id, $event)"
      >
        {{ markerDisplayLabel(marker) }}
      </button>
    </div>

    <ul v-if="markers.length > 0" class="image-marker-legend">
      <li v-for="marker in markers" :key="marker.id" class="image-marker-legend-item">
        <template v-if="editable">
          <span
            class="image-marker-legend-icon"
            :class="{
              'image-marker-legend-icon--house': marker.kind === 'house',
              'image-marker-legend-icon--number': marker.kind === 'number',
            }"
          >
            {{ markerDisplayLabel(marker) }}
          </span>
          <input
            :value="marker.text"
            type="text"
            class="image-marker-legend-input"
            placeholder="説明を入力"
            @input="updateMarkerText(marker.id, ($event.target as HTMLInputElement).value)"
          />
          <button
            type="button"
            class="image-marker-remove-btn"
            aria-label="マーカーを削除"
            @click="removeMarker(marker.id)"
          >
            削除
          </button>
        </template>
        <template v-else>
          <span
            class="image-marker-legend-icon"
            :class="{
              'image-marker-legend-icon--house': marker.kind === 'house',
              'image-marker-legend-icon--number': marker.kind === 'number',
            }"
          >
            {{ markerDisplayLabel(marker) }}
          </span>
          <span class="image-marker-legend-text">{{ marker.text || '（説明なし）' }}</span>
        </template>
      </li>
    </ul>
  </div>
</template>
