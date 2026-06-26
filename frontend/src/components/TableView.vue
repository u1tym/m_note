<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { getTable } from '../api/noteApi'
import { formatApiError } from '../api/errors'
import type { TableCellItem } from '../api/types'
import {
  alignAt,
  alignClass,
  buildCellMap,
  buildColWidthMap,
  colWidthStyle,
  isTableError,
} from '../utils/tablePart'

const props = defineProps<{
  tableId: number
  refreshToken?: number
}>()

const emit = defineEmits<{
  loaded: []
}>()

const loading = ref(true)
const error = ref<string | null>(null)
const title = ref('')
const rowCount = ref(5)
const colCount = ref(5)
const cellMap = ref<Map<string, TableCellItem>>(new Map())
const colWidthMap = ref<Map<number, number>>(new Map())

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await getTable(props.tableId)
    title.value = res.title
    rowCount.value = res.row_count
    colCount.value = res.col_count
    cellMap.value = buildCellMap(res.cells)
    colWidthMap.value = buildColWidthMap(res.col_widths)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
    emit('loaded')
  }
}

function displayAt(x: number, y: number): string {
  return cellMap.value.get(`${x},${y}`)?.display_value ?? ''
}

function widthAt(col: number): number | undefined {
  return colWidthMap.value.get(col)
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
  () => props.tableId,
  () => {
    void load()
  },
)
</script>

<template>
  <div class="table-view table-view--preview">
    <p v-if="loading" class="table-status">読み込み中…</p>
    <p v-else-if="error" class="table-status error">{{ error }}</p>
    <div v-else class="table-preview-wrap">
      <p v-if="title" class="table-title">{{ title }}</p>
      <table class="sheet-grid sheet-grid--preview">
        <tbody>
          <tr v-for="row in rowCount" :key="`r-${row}`">
            <td
              v-for="col in colCount"
              :key="`c-${col}-${row}`"
              class="sheet-cell"
              :class="[
                alignClass(alignAt(cellMap, col, row)),
                {
                  'sheet-cell--error': isTableError(displayAt(col, row)),
                  'sheet-col--sized': widthAt(col) !== undefined,
                },
              ]"
              :style="colWidthStyle(widthAt(col))"
            >
              {{ displayAt(col, row) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
