<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import {
  createChecklistCategory,
  createChecklistItem,
  deleteChecklistCategory,
  deleteChecklistItem,
  getChecklist,
  moveChecklistItem,
  reorderChecklistCategories,
  updateChecklistCategory,
  updateChecklistItem,
  updateChecklistTitle,
} from '../api/noteApi'
import { formatApiError } from '../api/errors'
import type {
  ChecklistCategoryItem,
  ChecklistMutationResponse,
} from '../api/types'

const props = defineProps<{
  checklistId: number
}>()

const emit = defineEmits<{
  updated: []
}>()

const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const checklistTitle = ref('')
const savedTitle = ref('')
const categories = ref<ChecklistCategoryItem[]>([])
const newCategoryName = ref('')
const newItemTitleByCat = ref<Record<number, string>>({})
const draftCategoryNames = ref<Record<number, string>>({})

type DragPayload =
  | { kind: 'category'; categoryId: number }
  | { kind: 'item'; itemId: number; fromCategoryId: number }

const dragPayload = ref<DragPayload | null>(null)
const dropHint = ref<string | null>(null)

const unnamedCategory = computed(
  () => categories.value.find((c) => c.is_unnamed) ?? null,
)
const namedCategories = computed(() =>
  categories.value.filter((c) => !c.is_unnamed),
)

function applyState(res: ChecklistMutationResponse, notify = false): void {
  checklistTitle.value = res.title
  savedTitle.value = res.title
  categories.value = res.categories
  const names: Record<number, string> = {}
  for (const cat of res.categories) {
    if (!cat.is_unnamed) {
      names[cat.id] = cat.name
    }
  }
  draftCategoryNames.value = names
  if (notify) {
    emit('updated')
  }
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await getChecklist(props.checklistId)
    applyState(res)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

async function mutate(
  action: () => Promise<ChecklistMutationResponse>,
): Promise<void> {
  saving.value = true
  error.value = null
  try {
    const res = await action()
    applyState(res, true)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    saving.value = false
  }
}

async function onTitleBlur(): Promise<void> {
  if (saving.value || checklistTitle.value === savedTitle.value) {
    return
  }
  await mutate(() => updateChecklistTitle(props.checklistId, checklistTitle.value))
}

async function onAddCategory(): Promise<void> {
  const name = newCategoryName.value.trim()
  if (!name || saving.value) {
    return
  }
  await mutate(() => createChecklistCategory(props.checklistId, name))
  newCategoryName.value = ''
}

async function onCategoryNameBlur(cat: ChecklistCategoryItem): Promise<void> {
  if (cat.is_unnamed || saving.value) {
    return
  }
  const next = (draftCategoryNames.value[cat.id] ?? '').trim()
  if (!next || next === cat.name) {
    draftCategoryNames.value = { ...draftCategoryNames.value, [cat.id]: cat.name }
    return
  }
  await mutate(() => updateChecklistCategory(props.checklistId, cat.id, next))
}

async function onDeleteCategory(categoryId: number): Promise<void> {
  if (saving.value) {
    return
  }
  if (!window.confirm('カテゴリとその中のチェック項目を削除しますか？')) {
    return
  }
  await mutate(() => deleteChecklistCategory(props.checklistId, categoryId))
}

async function onAddItem(categoryId: number | null): Promise<void> {
  if (saving.value) {
    return
  }
  const key = categoryId ?? -1
  const title = (newItemTitleByCat.value[key] ?? '').trim()
  await mutate(() =>
    createChecklistItem({
      checklistId: props.checklistId,
      categoryId,
      title,
    }),
  )
  newItemTitleByCat.value = { ...newItemTitleByCat.value, [key]: '' }
}

async function onItemTitleBlur(
  itemId: number,
  title: string,
  current: string,
): Promise<void> {
  if (saving.value || title === current) {
    return
  }
  await mutate(() =>
    updateChecklistItem({
      checklistId: props.checklistId,
      itemId,
      title,
    }),
  )
}

async function onToggleChecked(itemId: number, isChecked: boolean): Promise<void> {
  if (saving.value) {
    return
  }
  await mutate(() =>
    updateChecklistItem({
      checklistId: props.checklistId,
      itemId,
      isChecked,
    }),
  )
}

async function onDeleteItem(itemId: number): Promise<void> {
  if (saving.value) {
    return
  }
  await mutate(() => deleteChecklistItem(props.checklistId, itemId))
}

function onCategoryDragStart(categoryId: number, event: DragEvent): void {
  dragPayload.value = { kind: 'category', categoryId }
  event.dataTransfer?.setData('text/plain', `category:${categoryId}`)
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function onItemDragStart(
  itemId: number,
  fromCategoryId: number,
  event: DragEvent,
): void {
  dragPayload.value = { kind: 'item', itemId, fromCategoryId }
  event.dataTransfer?.setData('text/plain', `item:${itemId}`)
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function onDragEnd(): void {
  dragPayload.value = null
  dropHint.value = null
}

async function onCategoryDrop(targetCategoryId: number): Promise<void> {
  const payload = dragPayload.value
  dropHint.value = null
  if (!payload || payload.kind !== 'category' || saving.value) {
    return
  }
  if (payload.categoryId === targetCategoryId) {
    return
  }
  const ids = categories.value.map((c) => c.id)
  const from = ids.indexOf(payload.categoryId)
  const to = ids.indexOf(targetCategoryId)
  if (from < 0 || to < 0) {
    return
  }
  ids.splice(from, 1)
  ids.splice(to, 0, payload.categoryId)
  await mutate(() => reorderChecklistCategories(props.checklistId, ids))
}

async function onItemDrop(toCategoryId: number, toIndex: number): Promise<void> {
  const payload = dragPayload.value
  dropHint.value = null
  if (!payload || payload.kind !== 'item' || saving.value) {
    return
  }
  await mutate(() =>
    moveChecklistItem({
      checklistId: props.checklistId,
      itemId: payload.itemId,
      toCategoryId,
      toIndex,
    }),
  )
}

function onCategoryDragOver(categoryId: number, event: DragEvent): void {
  if (dragPayload.value?.kind !== 'category') {
    return
  }
  event.preventDefault()
  dropHint.value = `cat:${categoryId}`
}

function onItemDragOver(
  categoryId: number,
  index: number,
  event: DragEvent,
): void {
  if (dragPayload.value?.kind !== 'item') {
    return
  }
  event.preventDefault()
  dropHint.value = `item:${categoryId}:${index}`
}

function onListDragOver(categoryId: number, event: DragEvent): void {
  if (dragPayload.value?.kind !== 'item') {
    return
  }
  event.preventDefault()
  const cat = categories.value.find((c) => c.id === categoryId)
  const index = cat?.items.length ?? 0
  dropHint.value = `item:${categoryId}:${index}`
}

async function onListDrop(categoryId: number): Promise<void> {
  const cat = categories.value.find((c) => c.id === categoryId)
  await onItemDrop(categoryId, cat?.items.length ?? 0)
}

watch(
  () => props.checklistId,
  () => {
    void load()
  },
)

void load()
</script>

<template>
  <div class="checklist-editor">
    <p v-if="loading" class="table-status">読み込み中…</p>
    <template v-else>
      <p v-if="error" class="table-status error">{{ error }}</p>

      <label class="table-title-field">
        タイトル
        <input
          v-model="checklistTitle"
          type="text"
          class="table-title-input"
          :disabled="saving"
          placeholder="チェックリストのタイトル"
          @blur="onTitleBlur"
        />
      </label>

      <div class="checklist-toolbar">
        <input
          v-model="newCategoryName"
          type="text"
          class="table-title-input checklist-inline-input"
          :disabled="saving"
          placeholder="新しいカテゴリ名"
          @keydown.enter.prevent="onAddCategory"
        />
        <button type="button" :disabled="saving || !newCategoryName.trim()" @click="onAddCategory">
          カテゴリ追加
        </button>
      </div>

      <div class="checklist-editor-body">
        <section
          class="checklist-cat-block"
          @dragover="unnamedCategory ? onListDragOver(unnamedCategory.id, $event) : undefined"
          @drop.prevent="unnamedCategory ? onListDrop(unnamedCategory.id) : undefined"
        >
          <ul class="checklist-edit-items">
            <template v-if="unnamedCategory">
              <li
                v-for="(item, index) in unnamedCategory.items"
                :key="item.id"
                class="checklist-edit-item"
                :class="{
                  'checklist-drop-before':
                    dropHint === `item:${unnamedCategory.id}:${index}`,
                }"
                @dragover="onItemDragOver(unnamedCategory.id, index, $event)"
                @drop.prevent="onItemDrop(unnamedCategory.id, index)"
              >
                <span
                  class="checklist-drag-handle"
                  title="ドラッグで移動"
                  draggable="true"
                  @dragstart="onItemDragStart(item.id, unnamedCategory.id, $event)"
                  @dragend="onDragEnd"
                >
                  ⋮⋮
                </span>
                <input
                  type="checkbox"
                  :checked="item.is_checked"
                  :disabled="saving"
                  @change="
                    onToggleChecked(item.id, ($event.target as HTMLInputElement).checked)
                  "
                />
                <input
                  :value="item.title"
                  type="text"
                  class="checklist-item-input"
                  :disabled="saving"
                  placeholder="チェック項目"
                  @blur="
                    onItemTitleBlur(
                      item.id,
                      ($event.target as HTMLInputElement).value,
                      item.title,
                    )
                  "
                />
                <button
                  type="button"
                  class="checklist-icon-btn"
                  :disabled="saving"
                  @click="onDeleteItem(item.id)"
                >
                  削除
                </button>
              </li>
            </template>
          </ul>
          <div class="checklist-add-row">
            <input
              v-model="newItemTitleByCat[-1]"
              type="text"
              class="checklist-item-input"
              :disabled="saving"
              placeholder="未分類に項目を追加"
              @keydown.enter.prevent="onAddItem(null)"
            />
            <button type="button" :disabled="saving" @click="onAddItem(null)">追加</button>
          </div>
        </section>

        <section
          v-for="cat in namedCategories"
          :key="cat.id"
          class="checklist-cat-block"
          :class="{ 'checklist-drop-target': dropHint === `cat:${cat.id}` }"
          @dragover="onCategoryDragOver(cat.id, $event)"
          @drop.prevent="onCategoryDrop(cat.id)"
        >
          <div class="checklist-cat-header">
            <span
              class="checklist-drag-handle"
              title="ドラッグでカテゴリ順変更"
              draggable="true"
              @dragstart="onCategoryDragStart(cat.id, $event)"
              @dragend="onDragEnd"
            >
              ⋮⋮
            </span>
            <input
              v-model="draftCategoryNames[cat.id]"
              type="text"
              class="checklist-category-input"
              :disabled="saving"
              @blur="onCategoryNameBlur(cat)"
            />
            <button
              type="button"
              class="checklist-icon-btn"
              :disabled="saving"
              @click="onDeleteCategory(cat.id)"
            >
              カテゴリ削除
            </button>
          </div>
          <ul
            class="checklist-edit-items"
            @dragover="onListDragOver(cat.id, $event)"
            @drop.prevent="onListDrop(cat.id)"
          >
            <li
              v-for="(item, index) in cat.items"
              :key="item.id"
              class="checklist-edit-item"
              :class="{ 'checklist-drop-before': dropHint === `item:${cat.id}:${index}` }"
              @dragover="onItemDragOver(cat.id, index, $event)"
              @drop.prevent="onItemDrop(cat.id, index)"
            >
              <span
                class="checklist-drag-handle"
                title="ドラッグで移動"
                draggable="true"
                @dragstart="onItemDragStart(item.id, cat.id, $event)"
                @dragend="onDragEnd"
              >
                ⋮⋮
              </span>
              <input
                type="checkbox"
                :checked="item.is_checked"
                :disabled="saving"
                @change="
                  onToggleChecked(item.id, ($event.target as HTMLInputElement).checked)
                "
              />
              <input
                :value="item.title"
                type="text"
                class="checklist-item-input"
                :disabled="saving"
                placeholder="チェック項目"
                @blur="
                  onItemTitleBlur(
                    item.id,
                    ($event.target as HTMLInputElement).value,
                    item.title,
                  )
                "
              />
              <button
                type="button"
                class="checklist-icon-btn"
                :disabled="saving"
                @click="onDeleteItem(item.id)"
              >
                削除
              </button>
            </li>
          </ul>
          <div class="checklist-add-row">
            <input
              v-model="newItemTitleByCat[cat.id]"
              type="text"
              class="checklist-item-input"
              :disabled="saving"
              placeholder="このカテゴリに項目を追加"
              @keydown.enter.prevent="onAddItem(cat.id)"
            />
            <button type="button" :disabled="saving" @click="onAddItem(cat.id)">追加</button>
          </div>
        </section>
      </div>

      <p v-if="saving" class="table-saving">保存中…</p>
    </template>
  </div>
</template>
