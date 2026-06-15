import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

/** Windows では localhost が IPv6(::1) になり、IPv4 のみ待受の API と ETIMEDOUT になることがある */
function normalizeProxyTarget(raw: string): string {
  return raw.replace(/^http:\/\/localhost/i, 'http://127.0.0.1')
}

const DEFAULT_NOTE_PROXY_TARGET = 'http://127.0.0.1:8000'

/**
 * デバッグ時の接続方式（VITE_NOTE_ORIGIN）
 * - 既定 `/api/note` … Vite プロキシ経由。ブラウザから同一オリジンなので CORS 不要
 * - 代替 `http://127.0.0.1:8000` … 直接接続。バックエンドの CORS_ORIGINS 設定が必要
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const noteOrigin = env.VITE_NOTE_ORIGIN ?? ''
  const useProxy = noteOrigin.startsWith('/')
  const noteProxyTarget = normalizeProxyTarget(
    env.VITE_NOTE_PROXY_TARGET || DEFAULT_NOTE_PROXY_TARGET,
  )

  return {
    plugins: [vue()],
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: false,
      proxy: useProxy
        ? {
            '/api/note': {
              target: noteProxyTarget,
              changeOrigin: true,
              rewrite: (path) => path.replace(/^\/api\/note/, ''),
              // 画像 Base64 など大きな POST 向け（接続確立後の待ち）
              timeout: 120_000,
              proxyTimeout: 120_000,
            },
          }
        : undefined,
    },
  }
})
