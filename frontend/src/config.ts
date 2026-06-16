/** Note API のベース URL（末尾スラッシュなし） */
export const noteOrigin = (import.meta.env.VITE_NOTE_ORIGIN as string | undefined) ?? ''

/** ログイン／セッション API のベース URL（末尾スラッシュなし） */
export const loginOrigin = (import.meta.env.VITE_LOGIN_ORIGIN as string | undefined) ?? ''

/**
 * NOTE API 呼び出し前にセッション延長を行うか。
 * デバッグ時は既定で false（03_note_frontend.txt の要件）。
 */
export const skipSessionExtend =
  (import.meta.env.VITE_SKIP_SESSION_EXTEND as string | undefined) === 'true'

/** 別画面のログイン URL（未設定時はログイン API 起点を使用） */
export const loginPageUrl =
  (import.meta.env.VITE_LOGIN_PAGE_URL as string | undefined) ?? `${loginOrigin}/login`

/** メニュー画面 URL（戻るボタン遷移先）。.env では # 以降がコメントになるため "..." で囲むこと */
export const menuPageUrl =
  (import.meta.env.VITE_MENU_PAGE_URL as string | undefined) ?? '/mobile/login/#/menu'
