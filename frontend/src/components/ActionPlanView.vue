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
      <p
        v-if="formatPointTimes(point, index) || point.place"
        class="action-point-line"
      >
        <span v-if="formatPointTimes(point, index)" class="action-point-time">
          {{ formatPointTimes(point, index) }}
        </span>
        <span v-if="point.place" class="action-point-place">{{ point.place }}</span>
      </p>
      <p
        v-if="index < plan.legs.length && plan.legs[index].memo"
        class="action-leg-memo"
      >
        {{ plan.legs[index].memo }}
      </p>
      <p
        v-if="index < plan.legs.length && plan.legs[index].note"
        class="action-leg-note"
      >
        {{ plan.legs[index].note }}
      </p>
    </template>
  </div>
  <p v-else class="action-plan-error">行動予定の形式が不正です</p>
</template>
