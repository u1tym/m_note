import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

import { noteOrigin } from '../config'
import { isUnauthorizedError, redirectToLogin } from './auth'
import { extendSession } from './session'

const MAX_RETRIES = 2
const RETRY_DELAY_MS = 600

const RETRYABLE_ERROR_CODES = new Set(['ECONNREFUSED', 'ETIMEDOUT', 'ERR_NETWORK'])
const RETRYABLE_HTTP_STATUS = new Set([502, 503, 504])

type RetryableConfig = InternalAxiosRequestConfig & { _retryCount?: number }

let sessionExtendPromise: Promise<void> | null = null

async function ensureSessionExtended(): Promise<void> {
  if (!sessionExtendPromise) {
    sessionExtendPromise = extendSession().finally(() => {
      sessionExtendPromise = null
    })
  }
  await sessionExtendPromise
}

async function noteRequestInterceptor(
  config: InternalAxiosRequestConfig,
): Promise<InternalAxiosRequestConfig> {
  await ensureSessionExtended()
  return config
}

function isRetryableError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) {
    return false
  }
  if (error.code && RETRYABLE_ERROR_CODES.has(error.code)) {
    return true
  }
  const status = error.response?.status
  return status !== undefined && RETRYABLE_HTTP_STATUS.has(status)
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

export const noteClient: AxiosInstance = axios.create({
  baseURL: noteOrigin,
  withCredentials: true,
  timeout: 120_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

noteClient.interceptors.request.use(noteRequestInterceptor)

noteClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config as RetryableConfig | undefined

    if (config && isRetryableError(error)) {
      const retryCount = config._retryCount ?? 0
      if (retryCount < MAX_RETRIES) {
        config._retryCount = retryCount + 1
        await sleep(RETRY_DELAY_MS * config._retryCount)
        return noteClient.request(config)
      }
    }

    if (isUnauthorizedError(error)) {
      redirectToLogin()
    }
    return Promise.reject(error)
  },
)

export async function postNote<T>(path: string, body: unknown): Promise<T> {
  const { data } = await noteClient.post<T>(path, body)
  return data
}
