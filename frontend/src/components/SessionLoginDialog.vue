<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

import {
  cancelSessionLogin,
  sessionLoginDialog,
  submitSessionLogin,
} from '../api/sessionAuth'

const passwordInput = ref<HTMLInputElement | null>(null)

watch(
  () => sessionLoginDialog.open,
  async (open) => {
    if (!open) {
      return
    }
    await nextTick()
    passwordInput.value?.focus()
  },
)

async function onSubmit(): Promise<void> {
  await submitSessionLogin()
}

function onCancel(): void {
  cancelSessionLogin()
}
</script>

<template>
  <div
    v-if="sessionLoginDialog.open"
    class="login-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="session-login-title"
    @click.self="onCancel"
  >
    <form class="login-dialog" @submit.prevent="onSubmit">
      <h2 id="session-login-title">ログイン</h2>
      <p class="login-hint">セッションの有効期限が切れました。再ログインしてください。</p>

      <label class="login-field">
        <span>ユーザー名</span>
        <input
          v-model="sessionLoginDialog.username"
          type="text"
          name="username"
          autocomplete="username"
          :disabled="sessionLoginDialog.loading"
        />
      </label>

      <label class="login-field">
        <span>パスワード</span>
        <input
          ref="passwordInput"
          v-model="sessionLoginDialog.password"
          type="password"
          name="password"
          autocomplete="current-password"
          :disabled="sessionLoginDialog.loading"
        />
      </label>

      <p v-if="sessionLoginDialog.error" class="login-error">{{ sessionLoginDialog.error }}</p>

      <div class="login-actions">
        <button type="button" class="login-cancel" :disabled="sessionLoginDialog.loading" @click="onCancel">
          キャンセル
        </button>
        <button type="submit" class="login-submit" :disabled="sessionLoginDialog.loading">
          {{ sessionLoginDialog.loading ? 'ログイン中…' : 'ログイン' }}
        </button>
      </div>
    </form>
  </div>
</template>
