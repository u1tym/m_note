<script setup lang="ts">
import { ref, watch } from 'vue'

import {
  addNextPoint,
  normalizeActionPlanForEditor,
  removePoint,
  type ActionPlanData,
} from '../utils/actionPlan'

const props = defineProps<{
  modelValue: ActionPlanData
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ActionPlanData]
}>()

const localPlan = ref<ActionPlanData>(normalizeActionPlanForEditor(props.modelValue))

/** 地点2以降: 単一時刻 vs 到着・出発 */
const splitModeByIndex = ref<Record<number, boolean>>({})

function syncSplitModes(plan: ActionPlanData): void {
  const next: Record<number, boolean> = {}
  plan.points.forEach((point, index) => {
    if (index === 0) {
      return
    }
    next[index] = Boolean(point.arrive || point.depart || splitModeByIndex.value[index])
  })
  splitModeByIndex.value = next
}

watch(
  () => props.modelValue,
  (plan) => {
    localPlan.value = normalizeActionPlanForEditor(plan)
    syncSplitModes(localPlan.value)
  },
  { deep: true },
)

watch(
  localPlan,
  (plan) => syncSplitModes(plan),
  { immediate: true, deep: true },
)

function emitUpdate(): void {
  const normalized = normalizeActionPlanForEditor(localPlan.value)
  localPlan.value = normalized
  emit('update:modelValue', normalized)
}

function setPointField(
  index: number,
  field: 'place' | 'time' | 'arrive' | 'depart',
  value: string,
): void {
  const point = localPlan.value.points[index]
  if (!point) {
    return
  }
  point[field] = value
  if (index > 0 && field === 'time' && value) {
    delete point.arrive
    delete point.depart
    splitModeByIndex.value[index] = false
  }
  if (index > 0 && (field === 'arrive' || field === 'depart')) {
    delete point.time
    splitModeByIndex.value[index] = true
  }
  emitUpdate()
}

function setLegMemo(index: number, memo: string): void {
  if (!localPlan.value.legs[index]) {
    return
  }
  localPlan.value.legs[index].memo = memo
  emitUpdate()
}

function toggleSplitMode(index: number, useSplit: boolean): void {
  splitModeByIndex.value[index] = useSplit
  const point = localPlan.value.points[index]
  if (!point) {
    return
  }
  if (useSplit) {
    delete point.time
    if (!point.arrive) {
      point.arrive = ''
    }
    if (!point.depart) {
      point.depart = ''
    }
  } else {
    delete point.arrive
    delete point.depart
    if (!point.time) {
      point.time = ''
    }
  }
  emitUpdate()
}

function onAddPoint(): void {
  localPlan.value = addNextPoint(localPlan.value)
  emitUpdate()
}

function onRemovePoint(index: number): void {
  localPlan.value = removePoint(localPlan.value, index)
  emitUpdate()
}

function isSplitMode(index: number): boolean {
  return splitModeByIndex.value[index] ?? false
}
</script>

<template>
  <div class="action-plan-editor">
    <template v-for="(point, index) in localPlan.points" :key="index">
      <fieldset class="action-point-fieldset">
        <legend>
          地点{{ index + 1 }}
          <button
            v-if="index > 0"
            type="button"
            class="action-remove-point"
            @click="onRemovePoint(index)"
          >
            削除
          </button>
        </legend>

        <template v-if="index === 0">
          <label class="action-field">
            <span>時刻 <em class="required">必須</em></span>
            <input
              type="text"
              :value="point.time ?? ''"
              placeholder="例: 9:00"
              @input="setPointField(index, 'time', ($event.target as HTMLInputElement).value)"
            />
          </label>
          <label class="action-field">
            <span>場所 <em class="required">必須</em></span>
            <input
              type="text"
              :value="point.place"
              placeholder="例: 東京駅"
              @input="setPointField(index, 'place', ($event.target as HTMLInputElement).value)"
            />
          </label>
        </template>

        <template v-else>
          <div class="action-time-mode">
            <label>
              <input
                type="radio"
                :name="`time-mode-${index}`"
                :checked="!isSplitMode(index)"
                @change="toggleSplitMode(index, false)"
              />
              単一時刻
            </label>
            <label>
              <input
                type="radio"
                :name="`time-mode-${index}`"
                :checked="isSplitMode(index)"
                @change="toggleSplitMode(index, true)"
              />
              到着・出発
            </label>
          </div>

          <template v-if="!isSplitMode(index)">
            <label class="action-field">
              <span>時刻</span>
              <input
                type="text"
                :value="point.time ?? ''"
                placeholder="例: 10:30"
                @input="setPointField(index, 'time', ($event.target as HTMLInputElement).value)"
              />
            </label>
          </template>
          <template v-else>
            <label class="action-field">
              <span>到着</span>
              <input
                type="text"
                :value="point.arrive ?? ''"
                placeholder="例: 10:00"
                @input="setPointField(index, 'arrive', ($event.target as HTMLInputElement).value)"
              />
            </label>
            <label class="action-field">
              <span>出発</span>
              <input
                type="text"
                :value="point.depart ?? ''"
                placeholder="例: 10:30"
                @input="setPointField(index, 'depart', ($event.target as HTMLInputElement).value)"
              />
            </label>
          </template>

          <label class="action-field">
            <span>場所</span>
            <input
              type="text"
              :value="point.place"
              placeholder="例: 新宿"
              @input="setPointField(index, 'place', ($event.target as HTMLInputElement).value)"
            />
          </label>
        </template>
      </fieldset>

      <label
        v-if="index < localPlan.points.length - 1"
        class="action-field action-leg-field"
      >
        <span>経由{{ index + 1 }}-{{ index + 2 }}メモ</span>
        <input
          type="text"
          :value="localPlan.legs[index]?.memo ?? ''"
          placeholder="例: 山手線"
          @input="setLegMemo(index, ($event.target as HTMLInputElement).value)"
        />
      </label>
    </template>

    <button type="button" class="action-add-point" @click="onAddPoint">地点を追加</button>
  </div>
</template>
