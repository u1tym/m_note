import type { TableCellItem } from '../api/types'

export type TableCellType = 'string' | 'date' | 'time' | 'datetime' | 'number'

export interface TableState {
  table_id: number
  row_count: number
  col_count: number
  cells: TableCellItem[]
}

export const TABLE_CELL_TYPES: { value: TableCellType; label: string }[] = [
  { value: 'string', label: '文字列' },
  { value: 'date', label: '日付' },
  { value: 'time', label: '時刻' },
  { value: 'datetime', label: '日時' },
  { value: 'number', label: '数値' },
]

export const DISPLAY_FORMATS: Record<TableCellType, { value: string; label: string }[]> = {
  string: [],
  date: [
    { value: 'YYYY/MM/DD', label: 'YYYY/MM/DD' },
    { value: 'MM/DD', label: 'MM/DD' },
  ],
  time: [
    { value: 'hh:mm', label: 'hh:mm' },
    { value: 'hh:mm:ss', label: 'hh:mm:ss' },
  ],
  datetime: [
    { value: 'YYYY/MM/DD hh:mm', label: 'YYYY/MM/DD hh:mm' },
    { value: 'YYYY/MM/DD hh:mm:ss', label: 'YYYY/MM/DD hh:mm:ss' },
  ],
  number: [
    { value: '整数', label: '整数' },
    { value: '小数2桁', label: '小数2桁' },
    { value: 'カンマ付き整数', label: 'カンマ付き整数' },
    { value: 'カンマ付き小数2桁', label: 'カンマ付き小数2桁' },
  ],
}

export type TextAlign = '左寄せ' | '中央寄せ' | '右寄せ'

export const TEXT_ALIGNS: { value: TextAlign; label: string }[] = [
  { value: '左寄せ', label: '左寄せ' },
  { value: '中央寄せ', label: '中央寄せ' },
  { value: '右寄せ', label: '右寄せ' },
]

export const DEFAULT_TEXT_ALIGN: TextAlign = '左寄せ'

export function alignClass(textAlign: string | undefined): string {
  if (textAlign === '中央寄せ') {
    return 'sheet-cell--align-center'
  }
  if (textAlign === '右寄せ') {
    return 'sheet-cell--align-right'
  }
  return 'sheet-cell--align-left'
}

export function alignAt(
  cellMap: Map<string, TableCellItem>,
  x: number,
  y: number,
): string {
  return cellMap.get(cellKey(x, y))?.text_align ?? DEFAULT_TEXT_ALIGN
}

export function defaultDisplayFormat(cellType: TableCellType): string {
  const options = DISPLAY_FORMATS[cellType]
  return options[0]?.value ?? ''
}

export function cellKey(x: number, y: number): string {
  return `${x},${y}`
}

export function buildCellMap(cells: TableCellItem[]): Map<string, TableCellItem> {
  const map = new Map<string, TableCellItem>()
  for (const cell of cells) {
    map.set(cellKey(cell.x, cell.y), cell)
  }
  return map
}

export function isTableError(value: string): boolean {
  return value === '#CYCLE!' || value === '#VALUE!' || value === '#ERROR!' || value === '#REF!'
}

export function colLabel(col: number): string {
  let n = col
  let label = ''
  while (n > 0) {
    n -= 1
    label = String.fromCharCode(65 + (n % 26)) + label
    n = Math.floor(n / 26)
  }
  return label
}
