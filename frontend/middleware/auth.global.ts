export default defineNuxtRouteMiddleware(async (to) => {
  // With HttpOnly cookies, JS can't read the access token.
  // Use the non-HttpOnly user_info cookie for client route guarding.
  const userInfo = useCookie('user_info')

  // Public routes (no auth required)
  const publicPaths = new Set(['/login', '/health'])
  if (publicPaths.has(to.path)) return

  // If user not present, try to refresh silently
  if (!userInfo.value) {
    const config = useRuntimeConfig()
    const apiBase = (config as any).apiBase || config.public.apiBase
    try {
      await $fetch(`${apiBase}/auth/refresh`, {
        method: 'POST',
        credentials: 'include'
      })
    } catch {
      // ignore refresh failures here
    }
  }

  // Still unauthenticated? Redirect to login
  if (!userInfo.value) {
    return navigateTo('/login')
  }
})
