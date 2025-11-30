<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const token = useCookie('access_token')

const health = ref<{ status: string; service: string } | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    // We try to fetch health. It should be public, but if it requires auth in future we can pass token.
    // Currently /health is public in main.py
    const res = await $fetch<{ status: string; service: string }>(`${apiBase}/health`)
    health.value = res
  } catch (e) {
    console.error(e)
    error.value = 'Failed to reach backend API.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="grid">
    <div class="card">
      <h1 class="card-title">Welcome to Mazarbul</h1>
      <p class="card-sub">
        Track Business Cases, Purchase Orders, Resources, and Goods Receipts — without fighting Excel.
      </p>
      <p>
        This is your StarHub-inspired command center for procurement and resource tracking.
      </p>
      <div class="actions" style="margin-top: 1rem; display: flex; gap: 1rem;">
        <NuxtLink to="/purchase-orders" class="btn-primary">
          View Purchase Orders
        </NuxtLink>
      </div>
    </div>

    <div class="card">
      <h2 class="card-title">Backend status</h2>
      <p class="card-sub">FastAPI + SQLite</p>

      <p v-if="loading">Checking backend health…</p>
      <p v-else-if="error" style="color: #cc0000;">{{ error }}</p>
      <div v-else-if="health">
        <p><strong>Status:</strong> {{ health.status }}</p>
        <p><strong>Service:</strong> {{ health.service }}</p>
      </div>
      <p v-else>Unknown state.</p>
    </div>
  </section>
</template>
