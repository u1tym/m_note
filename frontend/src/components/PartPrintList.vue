<script setup lang="ts">
import { computed } from 'vue'

import type { PartInfo } from '../api/types'
import ActionPlanView from './ActionPlanView.vue'
import ImagePartView from './ImagePartView.vue'
import MarkdownPreview from './MarkdownPreview.vue'
import TableView from './TableView.vue'
import TexPreview from './TexPreview.vue'

const props = defineProps<{
  parts: PartInfo[]
}>()

const emit = defineEmits<{
  'table-loaded': [tableId: number]
}>()

const sortedParts = computed(() => [...props.parts].sort((a, b) => a.dorder - b.dorder))

function tableIdFromPart(data: string): number {
  return Number.parseInt(data, 10)
}

function onTableLoaded(part: PartInfo): void {
  emit('table-loaded', tableIdFromPart(part.data))
}
</script>

<template>
  <ul class="parts-list parts-list--print">
    <li v-for="part in sortedParts" :key="part.id" class="part-card part-card--print">
      <div class="part-view part-view--print">
        <template v-if="part.ptype === 'jpeg' || part.ptype === 'png'">
          <ImagePartView
            :ptype="part.ptype"
            :data="part.data"
            :title="part.title"
            :markers="part.markers ?? []"
          />
        </template>
        <template v-else-if="part.ptype === 'binary'">
          <span class="part-binary-name">{{ part.filename || '（名前なし）' }}</span>
        </template>
        <template v-else-if="part.ptype === 'url'">
          <span class="part-url">{{ part.data }}</span>
        </template>
        <template v-else-if="part.ptype === 'action'">
          <ActionPlanView :data="part.data" />
        </template>
        <template v-else-if="part.ptype === 'table'">
          <TableView
            :table-id="tableIdFromPart(part.data)"
            @loaded="onTableLoaded(part)"
          />
        </template>
        <template v-else-if="part.ptype === 'md'">
          <MarkdownPreview :source="part.data" />
        </template>
        <template v-else-if="part.ptype === 'tex'">
          <TexPreview :source="part.data" />
        </template>
        <template v-else>
          <pre class="part-text-view">{{ part.data }}</pre>
        </template>
      </div>
    </li>
  </ul>
</template>
