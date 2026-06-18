<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'

import { loadKnownUsername } from './api/sessionAuth'
import SessionLoginDialog from './components/SessionLoginDialog.vue'

onMounted(() => {
  void loadKnownUsername()
})
</script>

<template>
  <div class="app-shell">
    <RouterView v-slot="{ Component }">
      <KeepAlive include="HomeView">
        <component :is="Component" />
      </KeepAlive>
    </RouterView>
    <SessionLoginDialog />
  </div>
</template>
