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
  updateTableColWidth,
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
  buildColWidthMap,
  cellKey,
  colLabel,
  colWidthStyle,
  defaultDisplayFormat,
  isTableError,
  MAX_COL_WIDTH_PX,
  MIN_COL_WIDTH_PX,
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
const colWidthMap = ref<Map<number, number>>(new Map())

const primaryCell = ref<{ x: number; y: number } | null>(null)
const anchorCell = ref<{ x: number; y: number } | null>(null)
const selectedCells = ref<Set<string>>(new Set())
const isEditing = ref(false)

const selectedColOnly = ref<number | null>(null)
const colWidthDraft = ref('')
const savedColWidth = ref<number | null>(null)
const colWidthTargetCol = ref<number | null>(null)
const editInput = ref('')
const editInputEl = ref<HTMLInputElement | null>(null)
const tableScrollEl = ref<HTMLDivElement | null>(null)
const clipboard = ref<TableCellItem | null>(null)

const selectedCount = computed(() => selectedCells.value.size)

const selectedCell = computed(() => {
  if (!primaryCell.value) {
    return null
  }
  return cellMap.value.get(cellKey(primaryCell.value.x, primaryCell.value.y)) ?? null
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

const selectedCol = computed(() => primaryCell.value?.x ?? selectedColOnly.value)

function isCellSelected(x: number, y: number): boolean {
  return selectedCells.value.has(cellKey(x, y))
}

function isPrimaryCell(x: number, y: number): boolean {
  return primaryCell.value?.x === x && primaryCell.value?.y === y
}

function getSelectedCoords(): Array<{ x: number; y: number }> {
  return [...selectedCells.value]
    .map((key) => {
      const [x, y] = key.split(',').map(Number)
      return { x, y }
    })
    .sort((a, b) => a.y - b.y || a.x - b.x)
}

function buildRangeSet(from: { x: number; y: number }, to: { x: number; y: number }): Set<string> {
  const set = new Set<string>()
  const xMin = Math.min(from.x, to.x)
  const xMax = Math.max(from.x, to.x)
  const yMin = Math.min(from.y, to.y)
  const yMax = Math.max(from.y, to.y)
  for (let y = yMin; y <= yMax; y += 1) {
    for (let x = xMin; x <= xMax; x += 1) {
      set.add(cellKey(x, y))
    }
  }
  return set
}

function syncColWidthDraft(col: number | null): void {
  colWidthTargetCol.value = col
  if (col === null) {
    colWidthDraft.value = ''
    savedColWidth.value = null
    return
  }
  const width = colWidthMap.value.get(col)
  savedColWidth.value = width ?? null
  colWidthDraft.value = width !== undefined ? String(width) : ''
}

function parseColWidthDraft(): number | null | 'invalid' {
  const trimmed = String(colWidthDraft.value).trim()
  if (trimmed === '') {
    return null
  }
  const nextWidth = Number(trimmed)
  if (!Number.isInteger(nextWidth) || Number.isNaN(nextWidth)) {
    return 'invalid'
  }
  return nextWidth
}

async function commitColWidth(): Promise<void> {
  const col = colWidthTargetCol.value
  if (col === null || saving.value) {
    return
  }

  const parsed = parseColWidthDraft()
  if (parsed === 'invalid') {
    error.value = `列幅は ${MIN_COL_WIDTH_PX}〜${MAX_COL_WIDTH_PX} の整数で指定してください`
    return
  }

  const saved = colWidthMap.value.get(col) ?? null
  if (parsed === saved || (parsed === null && saved === null)) {
    return
  }

  if (parsed !== null && (parsed < MIN_COL_WIDTH_PX || parsed > MAX_COL_WIDTH_PX)) {
    error.value = `列幅は ${MIN_COL_WIDTH_PX}〜${MAX_COL_WIDTH_PX} px で指定してください`
    return
  }

  saving.value = true
  error.value = null
  try {
    const res = await updateTableColWidth({
      tableId: props.tableId,
      x: col,
      widthPx: parsed,
    })
    applyTableState(res, true)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

function applyTableState(res: TableMutationResponse, notifyParent = false): void {
  tableTitle.value = res.title
  savedTitle.value = res.title
  rowCount.value = res.row_count
  colCount.value = res.col_count
  cellMap.value = buildCellMap(res.cells)
  colWidthMap.value = buildColWidthMap(res.col_widths)
  syncColWidthDraft(selectedCol.value)
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

function bindEditInputEl(el: Element | null): void {
  editInputEl.value = el instanceof HTMLInputElement ? el : null
}

async function focusEditInput(selectAll: boolean): Promise<void> {
  await nextTick()
  await nextTick()
  const el = editInputEl.value
  if (!el) {
    return
  }
  el.focus()
  if (selectAll) {
    el.select()
  } else {
    const len = el.value.length
    el.setSelectionRange(len, len)
  }
}

function insertCellRef(x: number, y: number): void {
  const ref = `Cell(${x},${y})`
  const el = editInputEl.value
  if (!el) {
    editInput.value += ref
    return
  }
  const start = el.selectionStart ?? editInput.value.length
  const end = el.selectionEnd ?? start
  editInput.value = editInput.value.slice(0, start) + ref + editInput.value.slice(end)
  void nextTick(() => {
    el.focus()
    const pos = start + ref.length
    el.setSelectionRange(pos, pos)
  })
}

async function startEditing(initialValue?: string): Promise<void> {
  if (!primaryCell.value) {
    return
  }
  isEditing.value = true
  if (initialValue !== undefined) {
    editInput.value = initialValue
  } else {
    editInput.value = inputAt(primaryCell.value.x, primaryCell.value.y)
  }
  await focusEditInput(initialValue === undefined)
}

function cancelEditing(): void {
  if (!primaryCell.value || !isEditing.value) {
    return
  }
  editInput.value = inputAt(primaryCell.value.x, primaryCell.value.y)
  isEditing.value = false
  void nextTick(() => {
    tableScrollEl.value?.focus()
  })
}

function onCellMouseDown(x: number, y: number, event: MouseEvent): void {
  if (!isEditing.value || !primaryCell.value) {
    return
  }
  if (primaryCell.value.x === x && primaryCell.value.y === y) {
    return
  }
  // blur より先に処理し、入力欄のフォーカスを維持して Cell 参照を挿入する
  event.preventDefault()
  insertCellRef(x, y)
}

async function selectCell(x: number, y: number, event?: MouseEvent): Promise<void> {
  if (isEditing.value && primaryCell.value) {
    if (primaryCell.value.x === x && primaryCell.value.y === y) {
      await focusEditInput(false)
      return
    }
    // 別セルクリック時の Cell 参照挿入は mousedown で処理済み
    return
  }

  if (
    primaryCell.value?.x === x &&
    primaryCell.value?.y === y &&
    selectedCount.value === 1 &&
    !event?.shiftKey
  ) {
    await startEditing()
    return
  }

  await commitCurrentCellIfEditing()
  await commitColWidth()
  selectedColOnly.value = null

  if (event?.shiftKey && anchorCell.value) {
    selectedCells.value = buildRangeSet(anchorCell.value, { x, y })
  } else {
    anchorCell.value = { x, y }
    selectedCells.value = new Set([cellKey(x, y)])
  }

  primaryCell.value = { x, y }
  isEditing.value = false
  editInput.value = inputAt(x, y)
  syncColWidthDraft(x)

  await nextTick()
  tableScrollEl.value?.focus()
}

async function onCellDblClick(x: number, y: number): Promise<void> {
  if (isEditing.value) {
    return
  }
  await selectCell(x, y)
  await startEditing()
}

async function selectColumn(col: number): Promise<void> {
  await commitCurrentCellIfEditing()
  await commitColWidth()
  selectedColOnly.value = col
  primaryCell.value = null
  anchorCell.value = null
  selectedCells.value = new Set()
  isEditing.value = false
  editInput.value = ''
  syncColWidthDraft(col)
}

function widthAt(col: number): number | undefined {
  return colWidthMap.value.get(col)
}

async function commitSelectedCell(): Promise<boolean> {
  if (!primaryCell.value || saving.value || !isEditing.value) {
    return true
  }
  const { x, y } = primaryCell.value
  const current = cellMap.value.get(cellKey(x, y))
  const nextInput = editInput.value
  if (current && current.input_value === nextInput) {
    return true
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
    return true
  } catch (e) {
    error.value = formatApiError(e)
    return false
  } finally {
    saving.value = false
  }
}

async function commitCurrentCellIfEditing(): Promise<void> {
  if (!isEditing.value) {
    return
  }
  const ok = await commitSelectedCell()
  if (ok) {
    isEditing.value = false
  }
}

async function commitAndMoveDown(): Promise<void> {
  if (!primaryCell.value) {
    return
  }
  const ok = await commitSelectedCell()
  if (!ok) {
    return
  }
  isEditing.value = false

  const { x, y } = primaryCell.value
  if (y >= rowCount.value) {
    await nextTick()
    tableScrollEl.value?.focus()
    return
  }

  const nextY = y + 1
  primaryCell.value = { x, y: nextY }
  anchorCell.value = { x, y: nextY }
  selectedCells.value = new Set([cellKey(x, nextY)])
  isEditing.value = true
  editInput.value = inputAt(x, nextY)
  await focusEditInput(true)
}

async function moveSelection(dx: number, dy: number, extend: boolean): Promise<void> {
  if (!primaryCell.value || isEditing.value || saving.value) {
    return
  }

  const nextX = Math.min(colCount.value, Math.max(1, primaryCell.value.x + dx))
  const nextY = Math.min(rowCount.value, Math.max(1, primaryCell.value.y + dy))
  if (nextX === primaryCell.value.x && nextY === primaryCell.value.y) {
    return
  }

  selectedColOnly.value = null

  if (extend && anchorCell.value) {
    selectedCells.value = buildRangeSet(anchorCell.value, { x: nextX, y: nextY })
  } else {
    anchorCell.value = { x: nextX, y: nextY }
    selectedCells.value = new Set([cellKey(nextX, nextY)])
  }

  primaryCell.value = { x: nextX, y: nextY }
  editInput.value = inputAt(nextX, nextY)
  syncColWidthDraft(nextX)

  await nextTick()
  tableScrollEl.value?.focus()
}

async function deleteSelectedCells(): Promise<void> {
  const coords = getSelectedCoords()
  if (coords.length === 0 || saving.value || isEditing.value) {
    return
  }

  saving.value = true
  error.value = null
  try {
    let lastRes: TableMutationResponse | null = null
    for (const { x, y } of coords) {
      const current = cellMap.value.get(cellKey(x, y))
      if (!current?.input_value.trim()) {
        continue
      }
      lastRes = await updateTableCell({
        tableId: props.tableId,
        x,
        y,
        cellType: current.cell_type,
        inputValue: '',
        displayFormat: current.display_format,
        textAlign: current.text_align,
      })
    }
    if (lastRes) {
      applyTableState(lastRes, true)
    }
    if (primaryCell.value) {
      editInput.value = inputAt(primaryCell.value.x, primaryCell.value.y)
    }
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onCellBlur(): Promise<void> {
  await commitCurrentCellIfEditing()
}

async function onCellInputKeydown(event: KeyboardEvent): Promise<void> {
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    await commitAndMoveDown()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    cancelEditing()
  }
}

function onTableKeydown(event: KeyboardEvent): void {
  if (!primaryCell.value || saving.value) {
    return
  }

  if (isEditing.value) {
    if (event.key === 'Enter') {
      event.preventDefault()
      void commitAndMoveDown()
    } else if (event.key === 'Escape') {
      event.preventDefault()
      cancelEditing()
    }
    return
  }

  const arrowKeys: Record<string, [number, number]> = {
    ArrowUp: [0, -1],
    ArrowDown: [0, 1],
    ArrowLeft: [-1, 0],
    ArrowRight: [1, 0],
  }
  if (event.key in arrowKeys) {
    event.preventDefault()
    const [dx, dy] = arrowKeys[event.key]!
    void moveSelection(dx, dy, event.shiftKey)
    return
  }

  if (event.key === 'Delete') {
    event.preventDefault()
    void deleteSelectedCells()
    return
  }

  if (event.ctrlKey || event.metaKey || event.altKey) {
    return
  }
  if (event.key.length === 1) {
    event.preventDefault()
    void startEditing(event.key)
  }
}

async function updateSelectedCells(
  buildPayload: (
    current: TableCellItem | undefined,
    x: number,
    y: number,
  ) => {
    cellType?: string
    inputValue?: string
    displayFormat?: string
    textAlign?: string
  } | null,
): Promise<void> {
  const coords = getSelectedCoords()
  if (coords.length === 0) {
    return
  }

  saving.value = true
  error.value = null
  try {
    let lastRes: TableMutationResponse | null = null
    for (const { x, y } of coords) {
      const current = cellMap.value.get(cellKey(x, y))
      let input = current?.input_value ?? ''
      if (isPrimaryCell(x, y) && isEditing.value) {
        input = editInput.value
      }
      if (!input.trim()) {
        continue
      }
      const payload = buildPayload(current, x, y)
      if (!payload) {
        continue
      }
      lastRes = await updateTableCell({
        tableId: props.tableId,
        x,
        y,
        cellType: payload.cellType,
        inputValue: payload.inputValue ?? input,
        displayFormat: payload.displayFormat,
        textAlign: payload.textAlign,
      })
    }
    if (lastRes) {
      applyTableState(lastRes, true)
      if (primaryCell.value) {
        editInput.value = inputAt(primaryCell.value.x, primaryCell.value.y)
      }
    }
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onTypeChange(cellType: TableCellType): Promise<void> {
  await updateSelectedCells((current) => ({
    cellType,
    inputValue: current?.input_value,
    displayFormat: defaultDisplayFormat(cellType),
    textAlign: current?.text_align ?? '左寄せ',
  }))
}

async function onFormatChange(displayFormat: string): Promise<void> {
  await updateSelectedCells((current) => ({
    cellType: current?.cell_type ?? 'string',
    inputValue: current?.input_value,
    displayFormat,
    textAlign: current?.text_align ?? '左寄せ',
  }))
}

async function onAlignChange(textAlign: TextAlign): Promise<void> {
  await updateSelectedCells((current) => ({
    cellType: current?.cell_type ?? 'string',
    inputValue: current?.input_value,
    displayFormat: current?.display_format ?? '',
    textAlign,
  }))
}

function onCopy(): void {
  if (!primaryCell.value) {
    return
  }
  const { x, y } = primaryCell.value
  const cell = cellMap.value.get(cellKey(x, y))
  if (!cell) {
    clipboard.value = {
      x,
      y,
      cell_type: 'string',
      input_value: isEditing.value ? editInput.value : '',
      display_format: '',
      display_value: '',
      text_align: '左寄せ',
    }
    return
  }
  clipboard.value = { ...cell }
}

async function onPaste(): Promise<void> {
  const coords = getSelectedCoords()
  if (!clipboard.value || coords.length === 0) {
    return
  }

  saving.value = true
  error.value = null
  try {
    let lastRes: TableMutationResponse | null = null
    for (const { x, y } of coords) {
      lastRes = await pasteTableCell({
        tableId: props.tableId,
        x,
        y,
        sourceInputValue: clipboard.value.input_value,
        sourceCellType: clipboard.value.cell_type,
        sourceDisplayFormat: clipboard.value.display_format,
        sourceTextAlign: clipboard.value.text_align,
        offsetX: x - clipboard.value.x,
        offsetY: y - clipboard.value.y,
      })
    }
    if (lastRes) {
      applyTableState(lastRes, true)
      if (primaryCell.value) {
        editInput.value = inputAt(primaryCell.value.x, primaryCell.value.y)
      }
    }
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

async function onColWidthBlur(): Promise<void> {
  await commitColWidth()
}

async function onResetColWidth(): Promise<void> {
  if (saving.value || selectedCol.value === null || savedColWidth.value === null) {
    return
  }
  colWidthDraft.value = ''
  await commitColWidth()
}

async function mutateTable(action: () => Promise<TableMutationResponse>): Promise<void> {
  await commitCurrentCellIfEditing()
  await commitColWidth()
  saving.value = true
  error.value = null
  try {
    const res = await action()
    applyTableState(res, true)
    if (primaryCell.value) {
      editInput.value = inputAt(primaryCell.value.x, primaryCell.value.y)
    }
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onInsertRow(): Promise<void> {
  const atRow = primaryCell.value?.y ?? rowCount.value + 1
  await mutateTable(() => insertTableRow(props.tableId, atRow))
}

async function onDeleteRow(): Promise<void> {
  if (!primaryCell.value) {
    return
  }
  await mutateTable(() => deleteTableRow(props.tableId, primaryCell.value!.y))
}

async function onInsertCol(): Promise<void> {
  const atCol = primaryCell.value?.x ?? colCount.value + 1
  await mutateTable(() => insertTableCol(props.tableId, atCol))
}

async function onDeleteCol(): Promise<void> {
  if (!primaryCell.value) {
    return
  }
  await mutateTable(() => deleteTableCol(props.tableId, primaryCell.value!.x))
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
        <button type="button" :disabled="selectedCount === 0 || saving" @click="onCopy">コピー</button>
        <button
          type="button"
          :disabled="selectedCount === 0 || !clipboard || saving"
          @click="onPaste"
        >
          ペースト
        </button>
        <button type="button" :disabled="saving" @click="onInsertRow">行追加</button>
        <button type="button" :disabled="!primaryCell || saving" @click="onDeleteRow">行削除</button>
        <button type="button" :disabled="saving" @click="onInsertCol">列追加</button>
        <button type="button" :disabled="!primaryCell || saving" @click="onDeleteCol">列削除</button>
      </div>

      <div v-if="selectedCol" class="table-col-props">
        <label>
          列 {{ colLabel(selectedCol) }} の幅 (px)
          <input
            v-model="colWidthDraft"
            type="number"
            class="table-col-width-input"
            :min="MIN_COL_WIDTH_PX"
            :max="MAX_COL_WIDTH_PX"
            :disabled="saving"
            :placeholder="`${MIN_COL_WIDTH_PX}〜${MAX_COL_WIDTH_PX}（空欄で既定）`"
            @blur="onColWidthBlur"
            @keydown.enter.prevent="onColWidthBlur"
          />
        </label>
        <button
          type="button"
          :disabled="saving || savedColWidth === null"
          @click="onResetColWidth"
        >
          列幅を既定に戻す
        </button>
      </div>

      <div v-if="selectedCount > 0" class="table-cell-props">
        <p v-if="selectedCount > 1" class="table-selection-hint">{{ selectedCount }} セル選択中</p>
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

      <div
        ref="tableScrollEl"
        class="table-scroll"
        tabindex="0"
        @keydown="onTableKeydown"
      >
        <table class="sheet-grid">
          <thead>
            <tr>
              <th class="sheet-corner" />
              <th
                v-for="col in colCount"
                :key="`h-${col}`"
                class="sheet-col-head"
                :class="{
                  'sheet-col-head--selected': selectedCol === col,
                  'sheet-col--sized': widthAt(col) !== undefined,
                }"
                :style="colWidthStyle(widthAt(col))"
                @click="void selectColumn(col)"
              >
                {{ colLabel(col) }}
              </th>
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
                    'sheet-cell--selected': isCellSelected(col, row),
                    'sheet-cell--primary': isPrimaryCell(col, row),
                    'sheet-cell--editing': isEditing && isPrimaryCell(col, row),
                    'sheet-cell--error': isTableError(displayAt(col, row)),
                    'sheet-col--sized': widthAt(col) !== undefined,
                  },
                ]"
                :style="colWidthStyle(widthAt(col))"
                @mousedown="onCellMouseDown(col, row, $event)"
                @click="void selectCell(col, row, $event)"
                @dblclick="void onCellDblClick(col, row)"
              >
                <input
                  v-if="isEditing && isPrimaryCell(col, row)"
                  :ref="(el) => bindEditInputEl(el as Element | null)"
                  v-model="editInput"
                  class="sheet-cell-input"
                  :class="alignClass(alignAt(cellMap, col, row))"
                  @blur="onCellBlur"
                  @keydown="onCellInputKeydown"
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
