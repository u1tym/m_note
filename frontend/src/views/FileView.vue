<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import {
  createPart,
  deletePart,
  getFile,
  swapPartOrder,
  updatePart,
} from '../api/noteApi'
import type { FileGetResponse, ImageMarker, PartInfo, PartsType } from '../api/types'
import { formatApiError } from '../api/errors'
import FilePrintDocument from '../components/FilePrintDocument.vue'
import PartEditor from '../components/PartEditor.vue'
import { waitUntil } from '../utils/waitUntil'

const props = defineProps<{
  fileId: string
}>()

const router = useRouter()
const file = ref<FileGetResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const exportingPdf = ref(false)
const printReady = ref(false)

const numericFileId = computed(() => Number(props.fileId))

const activeParts = computed(() =>
  (file.value?.parts ?? []).filter((p) => !p.is_del),
)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    file.value = await getFile(numericFileId.value, false)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'ファイル取得に失敗しました'
  } finally {
    loading.value = false
  }
}

async function onAddPart(
  type: PartsType,
  data: string,
  filename: string,
  title: string,
  markers: ImageMarker[],
  imageScale: number,
): Promise<void> {
  try {
    const res = await createPart(
      numericFileId.value,
      type,
      data,
      filename,
      title,
      markers,
      imageScale,
    )
    if (!res.result) {
      throw new Error(res.reason ?? 'パーツ作成に失敗しました')
    }
    await load()
  } catch (e) {
    error.value = formatApiError(e)
  }
}

async function onUpdatePart(
  part: PartInfo,
  type: PartsType,
  data: string,
  filename: string,
  title: string,
  markers: ImageMarker[],
  imageScale: number,
): Promise<void> {
  try {
    const res = await updatePart(part.id, type, data, filename, title, markers, imageScale)
    if (!res.result) {
      throw new Error(res.reason ?? 'パーツ更新に失敗しました')
    }
    await load()
  } catch (e) {
    error.value = formatApiError(e)
  }
}

async function onDeletePart(partsId: number): Promise<void> {
  try {
    const res = await deletePart(partsId)
    if (!res.result) {
      throw new Error(res.reason ?? 'パーツ削除に失敗しました')
    }
    await load()
  } catch (e) {
    error.value = formatApiError(e)
  }
}

async function onReorderParts(partsId1: number, partsId2: number): Promise<void> {
  try {
    const res = await swapPartOrder(numericFileId.value, partsId1, partsId2)
    if (!res.result) {
      throw new Error(res.reason ?? '表示順の変更に失敗しました')
    }
    await load()
  } catch (e) {
    error.value = formatApiError(e)
  }
}

function goBack(): void {
  if (window.history.state?.back != null) {
    router.back()
    return
  }
  router.push({ name: 'home' })
}

async function onExportPdf(): Promise<void> {
  if (!file.value || loading.value) {
    return
  }
  exportingPdf.value = true
  error.value = null
  try {
    if (!printReady.value) {
      const ready = await waitUntil(() => printReady.value)
      if (!ready) {
        throw new Error('PDF出力の準備に失敗しました')
      }
    }
    window.print()
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    exportingPdf.value = false
  }
}

watch(
  () => file.value?.id,
  () => {
    printReady.value = false
  },
)

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="page">
    <div class="screen-only">
      <header class="page-header">
        <div class="page-header-toolbar">
          <button type="button" class="back-btn" @click="goBack">← 戻る</button>
          <button
            type="button"
            class="pdf-export-btn"
            :disabled="loading || exportingPdf || !file"
            @click="onExportPdf"
          >
            {{ exportingPdf ? '準備中…' : 'PDF出力' }}
          </button>
        </div>
        <p v-if="file" class="subtitle">{{ file.belong.name }}</p>
        <h1>{{ file?.title ?? 'ファイル' }}</h1>
      </header>

      <p v-if="loading" class="status">読み込み中…</p>
      <p v-else-if="error" class="status error">{{ error }}</p>

      <PartEditor
        v-else-if="file"
        :parts="activeParts"
        @add="onAddPart"
        @update="onUpdatePart"
        @delete="onDeletePart"
        @reorder="onReorderParts"
      />
    </div>

    <div v-if="file" class="print-only" aria-hidden="true">
      <FilePrintDocument
        :folder-name="file.belong.name"
        :file-title="file.title"
        :parts="activeParts"
        @ready="printReady = true"
      />
    </div>
  </div>
</template>
