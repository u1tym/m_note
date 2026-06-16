<script setup lang="ts">
import { computed } from 'vue'

import {
  formatPointTimes,
  parseActionPlan,
} from '../utils/actionPlan'

const props = defineProps<{
  data: string
}>()

const plan = computed(() => parseActionPlan(props.data))
</script>

<template>
  <div v-if="plan" class="action-plan-view">
    <template v-for="(point, index) in plan.points" :key="index">
      <div class="action-point">
        <span class="action-point-label">地点{{ index + 1 }}</span>
        <p v-if="formatPointTimes(point, index)" class="action-point-time">
          {{ formatPointTimes(point, index) }}
        </p>
        <p v-if="point.place" class="action-point-place">{{ point.place }}</p>
      </div>
      <div
        v-if="index < plan.legs.length && plan.legs[index].memo"
        class="action-leg"
      >
        <span class="action-leg-label">経由</span>
        <p class="action-leg-memo">{{ plan.legs[index].memo }}</p>
      </div>
    </template>
  </div>
  <p v-else class="action-plan-error">行動予定の形式が不正です</p>
</template>
