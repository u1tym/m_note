<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import {
  deleteTableCol,
  deleteTableRow,
  getTable,
  insertTableCol,
  insertTableRow,
  pasteTableCell,
  updateTableCell,
  updateTableTitle,
} from '../api/noteApi'
import { formatApiError } from '../api/errors'
import type { TableCellItem, TableMutationResponse } from '../api/types'
import {
  DISPLAY_FORMATS,
  TABLE_CELL_TYPES,
  TEXT_ALIGNS,
  alignAt,
  alignClass,
  buildCellMap,
  cellKey,
  colLabel,
  defaultDisplayFormat,
  isTableError,
  type TableCellType,
  type TextAlign,
} from '../utils/tablePart'

const props = defineProps<{
  tableId: number
}>()

const emit = defineEmits<{
  updated: []
}>()

const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const tableTitle = ref('')
const savedTitle = ref('')
const rowCount = ref(5)
const colCount = ref(5)
const cellMap = ref<Map<string, TableCellItem>>(new Map())
const selected = ref<{ x: number; y: number } | null>(null)
const editInput = ref('')
const editInputEl = ref<HTMLInputElement | null>(null)
const clipboard = ref<TableCellItem | null>(null)

const selectedCell = computed(() => {
  if (!selected.value) {
    return null
  }
  return cellMap.value.get(cellKey(selected.value.x, selected.value.y)) ?? null
})

const selectedCellType = computed({
  get: () => selectedCell.value?.cell_type ?? 'string',
  set: (value: TableCellType) => {
    void onTypeChange(value)
  },
})

const selectedDisplayFormat = computed({
  get: () => selectedCell.value?.display_format ?? '',
  set: (value: string) => {
    void onFormatChange(value)
  },
})

const selectedTextAlign = computed({
  get: () => (selectedCell.value?.text_align ?? '左寄せ') as TextAlign,
  set: (value: TextAlign) => {
    void onAlignChange(value)
  },
})

function applyTableState(res: TableMutationResponse, notifyParent = false): void {
  tableTitle.value = res.title
  savedTitle.value = res.title
  rowCount.value = res.row_count
  colCount.value = res.col_count
  cellMap.value = buildCellMap(res.cells)
  if (notifyParent) {
    emit('updated')
  }
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await getTable(props.tableId)
    applyTableState(res)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

function displayAt(x: number, y: number): string {
  return cellMap.value.get(cellKey(x, y))?.display_value ?? ''
}

function inputAt(x: number, y: number): string {
  return cellMap.value.get(cellKey(x, y))?.input_value ?? ''
}

async function selectCell(x: number, y: number): Promise<void> {
  selected.value = { x, y }
  editInput.value = inputAt(x, y)
  await nextTick()
  editInputEl.value?.focus()
}

async function commitSelectedCell(): Promise<void> {
  if (!selected.value || saving.value) {
    return
  }
  const { x, y } = selected.value
  const current = cellMap.value.get(cellKey(x, y))
  const nextInput = editInput.value
  if (current && current.input_value === nextInput) {
    return
  }

  saving.value = true
  error.value = null
  try {
    const res = await updateTableCell({
      tableId: props.tableId,
      x,
      y,
      cellType: current?.cell_type,
      inputValue: nextInput,
      displayFormat: current?.display_format,
      textAlign: current?.text_align ?? '左寄せ',
    })
    applyTableState(res, true)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onCellBlur(): Promise<void> {
  await commitSelectedCell()
}

async function onTypeChange(cellType: TableCellType): Promise<void> {
  if (!selected.value) {
    return
  }
  const { x, y } = selected.value
  const current = cellMap.value.get(cellKey(x, y))
  const input = current?.input_value ?? editInput.value
  if (!input.trim()) {
    return
  }
  saving.value = true
  error.value = null
  try {
    const res = await updateTableCell({
      tableId: props.tableId,
      x,
      y,
      cellType,
      inputValue: input,
      displayFormat: defaultDisplayFormat(cellType),
      textAlign: current?.text_align ?? '左寄せ',
    })
    applyTableState(res, true)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onFormatChange(displayFormat: string): Promise<void> {
  if (!selected.value) {
    return
  }
  const { x, y } = selected.value
  const current = cellMap.value.get(cellKey(x, y))
  const input = current?.input_value ?? editInput.value
  if (!input.trim()) {
    return
  }
  saving.value = true
  error.value = null
  try {
    const res = await updateTableCell({
      tableId: props.tableId,
      x,
      y,
      cellType: current?.cell_type ?? 'string',
      inputValue: input,
      displayFormat,
      textAlign: current?.text_align ?? '左寄せ',
    })
    applyTableState(res, true)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onAlignChange(textAlign: TextAlign): Promise<void> {
  if (!selected.value) {
    return
  }
  const { x, y } = selected.value
  const current = cellMap.value.get(cellKey(x, y))
  const input = current?.input_value ?? editInput.value
  if (!input.trim()) {
    return
  }
  saving.value = true
  error.value = null
  try {
    const res = await updateTableCell({
      tableId: props.tableId,
      x,
      y,
      cellType: current?.cell_type ?? 'string',
      inputValue: input,
      displayFormat: current?.display_format ?? '',
      textAlign,
    })
    applyTableState(res, true)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

function onCopy(): void {
  if (!selected.value) {
    return
  }
  const cell = cellMap.value.get(cellKey(selected.value.x, selected.value.y))
  if (!cell) {
    clipboard.value = {
      x: selected.value.x,
      y: selected.value.y,
      cell_type: 'string',
      input_value: editInput.value,
      display_format: '',
      display_value: '',
      text_align: '左寄せ',
    }
    return
  }
  clipboard.value = { ...cell }
}

async function onPaste(): Promise<void> {
  if (!selected.value || !clipboard.value) {
    return
  }
  saving.value = true
  error.value = null
  try {
    const res = await pasteTableCell({
      tableId: props.tableId,
      x: selected.value.x,
      y: selected.value.y,
      sourceInputValue: clipboard.value.input_value,
      sourceCellType: clipboard.value.cell_type,
      sourceDisplayFormat: clipboard.value.display_format,
      sourceTextAlign: clipboard.value.text_align,
      offsetX: selected.value.x - clipboard.value.x,
      offsetY: selected.value.y - clipboard.value.y,
    })
    applyTableState(res, true)
    editInput.value = inputAt(selected.value.x, selected.value.y)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onTitleBlur(): Promise<void> {
  if (saving.value || tableTitle.value === savedTitle.value) {
    return
  }
  const nextTitle = tableTitle.value
  saving.value = true
  error.value = null
  try {
    const res = await updateTableTitle(props.tableId, nextTitle)
    applyTableState(res, true)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function mutateTable(action: () => Promise<TableMutationResponse>): Promise<void> {
  saving.value = true
  error.value = null
  try {
    const res = await action()
    applyTableState(res, true)
    if (selected.value) {
      editInput.value = inputAt(selected.value.x, selected.value.y)
    }
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onInsertRow(): Promise<void> {
  const atRow = selected.value?.y ?? rowCount.value + 1
  await mutateTable(() => insertTableRow(props.tableId, atRow))
}

async function onDeleteRow(): Promise<void> {
  if (!selected.value) {
    return
  }
  await mutateTable(() => deleteTableRow(props.tableId, selected.value!.y))
}

async function onInsertCol(): Promise<void> {
  const atCol = selected.value?.x ?? colCount.value + 1
  await mutateTable(() => insertTableCol(props.tableId, atCol))
}

async function onDeleteCol(): Promise<void> {
  if (!selected.value) {
    return
  }
  await mutateTable(() => deleteTableCol(props.tableId, selected.value!.x))
}

watch(
  () => props.tableId,
  () => {
    void load()
  },
)

void load()
</script>

<template>
  <div class="table-editor">
    <p v-if="loading" class="table-status">読み込み中…</p>
    <template v-else>
      <p v-if="error" class="table-status error">{{ error }}</p>

      <label class="table-title-field">
        タイトル
        <input
          v-model="tableTitle"
          type="text"
          class="table-title-input"
          :disabled="saving"
          placeholder="表のタイトル"
          @blur="onTitleBlur"
        />
      </label>

      <div class="table-toolbar">
        <button type="button" :disabled="!selected || saving" @click="onCopy">コピー</button>
        <button type="button" :disabled="!selected || !clipboard || saving" @click="onPaste">
          ペースト
        </button>
        <button type="button" :disabled="saving" @click="onInsertRow">行追加</button>
        <button type="button" :disabled="!selected || saving" @click="onDeleteRow">行削除</button>
        <button type="button" :disabled="saving" @click="onInsertCol">列追加</button>
        <button type="button" :disabled="!selected || saving" @click="onDeleteCol">列削除</button>
      </div>

      <div v-if="selected" class="table-cell-props">
        <label>
          型
          <select v-model="selectedCellType" :disabled="saving">
            <option v-for="opt in TABLE_CELL_TYPES" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </label>
        <label v-if="DISPLAY_FORMATS[selectedCellType as TableCellType].length > 0">
          表示形式
          <select v-model="selectedDisplayFormat" :disabled="saving">
            <option
              v-for="opt in DISPLAY_FORMATS[selectedCellType as TableCellType]"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </label>
        <label>
          表示位置
          <select v-model="selectedTextAlign" :disabled="saving">
            <option v-for="opt in TEXT_ALIGNS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </label>
        <span v-if="saving" class="table-saving">保存中…</span>
      </div>

      <div class="table-scroll">
        <table class="sheet-grid">
          <thead>
            <tr>
              <th class="sheet-corner" />
              <th v-for="col in colCount" :key="`h-${col}`">{{ colLabel(col) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rowCount" :key="`r-${row}`">
              <th class="sheet-row-head">{{ row }}</th>
              <td
                v-for="col in colCount"
                :key="`c-${col}-${row}`"
                class="sheet-cell"
                :class="[
                  alignClass(alignAt(cellMap, col, row)),
                  {
                    'sheet-cell--selected': selected?.x === col && selected?.y === row,
                    'sheet-cell--error': isTableError(displayAt(col, row)),
                  },
                ]"
                @click="selectCell(col, row)"
              >
                <input
                  v-if="selected?.x === col && selected?.y === row"
                  ref="editInputEl"
                  v-model="editInput"
                  class="sheet-cell-input"
                  :class="alignClass(alignAt(cellMap, col, row))"
                  @blur="onCellBlur"
                />
                <span v-else class="sheet-cell-display">{{ displayAt(col, row) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
