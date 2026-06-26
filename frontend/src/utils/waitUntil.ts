export function waitMs(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

export async function waitUntil(
  predicate: () => boolean,
  timeoutMs = 15000,
  intervalMs = 50,
): Promise<boolean> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (predicate()) {
      return true
    }
    await waitMs(intervalMs)
  }
  return predicate()
}
