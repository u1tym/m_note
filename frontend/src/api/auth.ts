import { loginPageUrl } from '../config'

export function redirectToLogin(): void {
  const returnUrl = encodeURIComponent(window.location.href)
  const separator = loginPageUrl.includes('?') ? '&' : '?'
  window.location.href = `${loginPageUrl}${separator}return=${returnUrl}`
}

export function isUnauthorizedError(error: unknown): boolean {
  if (typeof error !== 'object' || error === null || !('response' in error)) {
    return false
  }
  const response = (error as { response?: { status?: number } }).response
  return response?.status === 401
}
