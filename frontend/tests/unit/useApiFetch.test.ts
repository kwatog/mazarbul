import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useApiFetch } from '../../app/composables/useApiFetch'

describe('useApiFetch', () => {
  const apiBase = 'http://localhost:8000'

  beforeEach(() => {
    // Mock useRuntimeConfig
    vi.stubGlobal('useRuntimeConfig', () => ({
      public: { apiBase },
      apiBase // For SSR context if needed
    }))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('performs a basic fetch', async () => {
    const mockFetch = vi.fn().mockResolvedValue('success')
    vi.stubGlobal('$fetch', mockFetch)

    const result = await useApiFetch('/test')
    
    expect(result).toBe('success')
    expect(mockFetch).toHaveBeenCalledWith(`${apiBase}/test`, expect.objectContaining({ credentials: 'include' }))
  })

  it('retries on 401 token expiry', async () => {
    const mockFetch = vi.fn()
      // First call: 401
      .mockRejectedValueOnce({ response: { status: 401 } })
      // Second call: Refresh token
      .mockResolvedValueOnce({})
      // Third call: Retry original
      .mockResolvedValueOnce('retry-success')
    
    vi.stubGlobal('$fetch', mockFetch)

    const result = await useApiFetch('/protected')
    
    expect(result).toBe('retry-success')
    expect(mockFetch).toHaveBeenCalledTimes(3)
    expect(mockFetch).toHaveBeenNthCalledWith(1, `${apiBase}/protected`, expect.anything())
    expect(mockFetch).toHaveBeenNthCalledWith(2, `${apiBase}/auth/refresh`, expect.objectContaining({ method: 'POST' }))
    expect(mockFetch).toHaveBeenNthCalledWith(3, `${apiBase}/protected`, expect.anything())
  })

  it('fails if refresh fails', async () => {
    const mockFetch = vi.fn()
      .mockRejectedValueOnce({ response: { status: 401 } })
      .mockRejectedValueOnce({ response: { status: 401 } }) // Refresh fails
    
    vi.stubGlobal('$fetch', mockFetch)

    await expect(useApiFetch('/protected')).rejects.toMatchObject({ response: { status: 401 } })
  })
})
