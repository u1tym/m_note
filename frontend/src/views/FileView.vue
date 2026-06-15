<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  createPart,
  deletePart,
  getFile,
  updatePart,
} from '../api/noteApi'
import type { FileGetResponse, PartInfo, PartsType } from '../api/types'
import { formatApiError } from '../api/errors'
import PartEditor from '../components/PartEditor.vue'

const props = defineProps<{
  fileId: string
}>()

const router = useRouter()
const file = ref<FileGetResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

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

async function onAddPart(type: PartsType, data: string, filename: string): Promise<void> {
  try {
    const res = await createPart(numericFileId.value, type, data, filename)
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
): Promise<void> {
  try {
    const res = await updatePart(part.id, type, data, filename)
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

function goBack(): void {
  router.push({ name: 'home' })
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <button type="button" class="back-btn" @click="goBack">← 戻る</button>
      <h1>{{ file?.title ?? 'ファイル' }}</h1>
      <p v-if="file" class="subtitle">{{ file.belong.name }}</p>
    </header>

    <p v-if="loading" class="status">読み込み中…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <PartEditor
      v-else-if="file"
      :parts="activeParts"
      @add="onAddPart"
      @update="onUpdatePart"
      @delete="onDeletePart"
    />
  </div>
</template>
