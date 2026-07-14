<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { getChecklist } from '../api/noteApi'
import { formatApiError } from '../api/errors'
import type { ChecklistCategoryItem } from '../api/types'

const props = defineProps<{
  checklistId: number
  refreshToken?: number
}>()

const loading = ref(true)
const error = ref<string | null>(null)
const title = ref('')
const categories = ref<ChecklistCategoryItem[]>([])

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await getChecklist(props.checklistId)
    title.value = res.title
    categories.value = res.categories
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})

watch(
  () => props.refreshToken,
  () => {
    void load()
  },
)

watch(
  () => props.checklistId,
  () => {
    void load()
  },
)
</script>

<template>
  <div class="checklist-view">
    <p v-if="loading" class="table-status">読み込み中…</p>
    <p v-else-if="error" class="table-status error">{{ error }}</p>
    <div v-else class="checklist-preview">
      <p v-if="title" class="table-title">{{ title }}</p>
      <p v-if="categories.length === 0" class="checklist-empty">チェック項目はありません</p>
      <template v-for="cat in categories" :key="cat.id">
        <h3 v-if="!cat.is_unnamed" class="checklist-category-title">{{ cat.name }}</h3>
        <ul class="checklist-items">
          <li v-for="item in cat.items" :key="item.id" class="checklist-item">
            <span
              class="checklist-check"
              :class="{ 'checklist-check--on': item.is_checked }"
              aria-hidden="true"
            />
            <span
              class="checklist-item-title"
              :class="{ 'checklist-item-title--checked': item.is_checked }"
            >
              {{ item.title || '（無題）' }}
            </span>
          </li>
        </ul>
      </template>
    </div>
  </div>
</template>
