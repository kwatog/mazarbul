export function useApiFetch<T>(url: string, opts: Parameters<typeof $fetch<T>>[1] = {}) {
  const config = useRuntimeConfig()
  const apiBase = (config as any).apiBase || config.public.apiBase

  // Always include credentials so HttpOnly cookies are sent
  const baseOptions = { credentials: 'include' as const }

  const doFetch = async () => {
    try {
      return await $fetch<T>(`${apiBase}${url}`, { ...baseOptions, ...(opts || {}) })
    } catch (err: any) {
      // On 401, attempt a single refresh then retry once
      if (err?.response?.status === 401) {
        try {
          await $fetch(`${apiBase}/auth/refresh`, { method: 'POST', credentials: 'include' })
          return await $fetch<T>(`${apiBase}${url}`, { ...baseOptions, ...(opts || {}) })
        } catch (e) {
          throw err
        }
      }
      throw err
    }
  }

  return doFetch()
}

