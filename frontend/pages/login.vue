<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.apiBase || config.public.apiBase

const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)
const error = ref<string | null>(null)

const login = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await $fetch<{message: string, user: any}>(`${apiBase}/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        username: form.value.username,
        password: form.value.password
      })
    })
    
    // Backend sets HttpOnly access_token and user_info cookies.
    // As a precaution, also write user_info to keep UI in sync quickly.
    const userCookie = useCookie('user_info')
    userCookie.value = JSON.stringify(response.user)
    
    await navigateTo('/')
  } catch (e: any) {
    error.value = e.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="card-title">Welcome to Mazarbul</h1>
      <p class="card-sub">Please sign in to continue</p>
      
      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input 
            id="username" 
            v-model="form.username" 
            type="text" 
            required 
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input 
            id="password" 
            v-model="form.password" 
            type="password" 
            required 
            class="form-input"
          />
        </div>
        
        <p v-if="error" class="error-message">{{ error }}</p>
        
        <button 
          type="submit" 
          :disabled="loading" 
          class="btn-primary login-btn"
        >
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}

.login-card {
  background: var(--color-card);
  border-radius: 12px;
  box-shadow: var(--shadow-soft);
  padding: 2rem;
  width: 100%;
  max-width: 400px;
}

.login-form {
  margin-top: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.1);
}

.login-btn {
  width: 100%;
  margin-top: 1rem;
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin: 0.5rem 0;
}
</style>
