export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  app: {
    head: {
      title: 'Mazarbul',
      meta: [
        { name: 'description', content: 'Mazarbul - Chamber of Spend Records' }
      ]
    }
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE || 'http://localhost:8000'
    }
  },
  compatibilityDate: '2024-11-01'
})
