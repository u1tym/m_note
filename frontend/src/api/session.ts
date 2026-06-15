import axios from 'axios'

import { loginOrigin, skipSessionExtend } from '../config'
import { isUnauthorizedError, redirectToLogin } from './auth'

interface RefreshResponse {
  message: string
}

/**
 * セッション延長（JWT 更新）。
 * API_LOGIN_SPEC の POST /refresh を呼ぶ。
 * デバッグ時（VITE_SKIP_SESSION_EXTEND=true）は何もしない。
 */
export async function extendSession(): Promise<void> {
  if (skipSessionExtend || !loginOrigin) {
    return
  }

  try {
    await axios.post<RefreshResponse>(
      `${loginOrigin}/refresh`,
      {},
      { withCredentials: true },
    )
  } catch (error) {
    if (isUnauthorizedError(error)) {
      redirectToLogin()
    }
    throw error
  }
}
