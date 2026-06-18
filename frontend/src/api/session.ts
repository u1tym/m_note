import { ensureSessionValid } from './sessionAuth'

/**
 * セッション延長（JWT 更新）または再ログイン。
 * API_LOGIN_SPEC の POST /refresh を呼び、失敗時はログインダイアログを表示する。
 */
export async function extendSession(): Promise<void> {
  await ensureSessionValid()
}
