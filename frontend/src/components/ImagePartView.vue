<script setup lang="ts">
import { computed, ref } from 'vue'

import type { ImageMarker, ImageMarkerKind } from '../api/types'
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
    editable?: boolean
  }>(),
  {
    title: '',
    filename: '',
    showFilename: false,
    editable: false,
  },
)

const emit = defineEmits<{
  'update:markers': [markers: ImageMarker[]]
}>()

const placementKind = ref<ImageMarkerKind>('house')
const selectedId = ref<string | null>(null)

const imageSrc = computed(() => `data:image/${props.ptype};base64,${props.data}`)
const imageAlt = computed(
  () => props.title || props.filename || 'image part',
)

function onImageClick(event: MouseEvent): void {
  if (!props.editable) {
    return
  }
  const img = event.currentTarget as HTMLImageElement
  const rect = img.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    return
  }
  const x = (event.clientX - rect.left) / rect.width
  const y = (event.clientY - rect.top) / rect.height
  addMarker(x, y)
}

function addMarker(x: number, y: number): void {
  const clampedX = Math.min(1, Math.max(0, x))
  const clampedY = Math.min(1, Math.max(0, y))
  const marker: ImageMarker =
    placementKind.value === 'house'
      ? { id: newMarkerId(), kind: 'house', x: clampedX, y: clampedY, text: '' }
      : {
          id: newMarkerId(),
          kind: 'number',
          number: nextMarkerNumber(props.markers),
          x: clampedX,
          y: clampedY,
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

    <div class="image-part-frame">
      <img
        class="part-image"
        :class="{ 'part-image--placeable': editable }"
        :src="imageSrc"
        :alt="imageAlt"
        @click="onImageClick"
      />
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
        :style="{ left: `${marker.x * 100}%`, top: `${marker.y * 100}%` }"
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
