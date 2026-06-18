import axios from 'axios'

import { SessionAuthCancelledError } from './sessionAuth'

/** API 接続エラーをユーザー向けメッセージに変換 */
export function formatApiError(error: unknown): string {
  if (error instanceof SessionAuthCancelledError) {
    return ''
  }
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      return 'Note API (http://127.0.0.1:8000) に接続できません。uvicorn が起動しているか確認してください。'
    }
    if (error.code === 'ETIMEDOUT' || error.message.includes('timeout')) {
      return 'Note API への接続がタイムアウトしました。uvicorn が起動しているか、--reload による再起動直後でないか確認してください。'
    }
    if (error.response?.status === 502 || error.response?.status === 504) {
      return 'Note API へのプロキシ接続に失敗しました。バックエンド (127.0.0.1:8000) が応答しているか確認してください。'
    }
    if (error.response?.status === 401) {
      return '認証が必要です（DEBUG=true と DEBUG_AID を .env に設定するか、ログインしてください）'
    }
    if (error.response?.status === 500) {
      const detail = (error.response.data as { detail?: string })?.detail
      if (detail) {
        return detail
      }
    }
    if (error.response?.data && typeof error.response.data === 'object') {
      const detail = (error.response.data as { detail?: string }).detail
      if (detail) {
        return detail
      }
    }
  }
  if (error instanceof Error) {
    return error.message
  }
  return '操作に失敗しました'
}
