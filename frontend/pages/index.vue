<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const userCookie = useCookie('user_info')
const user = computed(() => userCookie.value)

// Statistics data
const stats = ref({
  totalBudget: 0,
  totalSpend: 0,
  openPOsCount: 0,
  openPOsValue: 0,
  recentGRsCount: 0,
  activeResourcesCount: 0,
  pendingBusinessCases: 0
})

const recentGoodsReceipts = ref<any[]>([])
const recentPurchaseOrders = ref<any[]>([])
const budgetItems = ref<any[]>([])

const loading = ref(true)
const error = ref<string | null>(null)

// Fetch all data
const fetchDashboardData = async () => {
  try {
    loading.value = true
    error.value = null

    // Fetch data in parallel
    const [
      budgetItemsData,
      posData,
      grsData,
      resourcesData,
      businessCasesData
    ] = await Promise.all([
      useApiFetch('/budget-items', { method: 'GET' }).catch(() => []),
      useApiFetch('/purchase-orders', { method: 'GET' }).catch(() => []),
      useApiFetch('/goods-receipts', { method: 'GET' }).catch(() => []),
      useApiFetch('/resources', { method: 'GET' }).catch(() => []),
      useApiFetch('/business-cases', { method: 'GET' }).catch(() => [])
    ])

    budgetItems.value = budgetItemsData as any[]
    const pos = posData as any[]
    const grs = grsData as any[]
    const resources = resourcesData as any[]
    const businessCases = businessCasesData as any[]

    // Calculate statistics
    stats.value.totalBudget = budgetItems.value.reduce((sum, item) => sum + (item.budget_amount || 0), 0)

    const openPOs = pos.filter(po => ['Open', 'Approved', 'In Progress'].includes(po.status))
    stats.value.openPOsCount = openPOs.length
    stats.value.openPOsValue = openPOs.reduce((sum, po) => sum + (po.total_amount || 0), 0)

    stats.value.totalSpend = pos.reduce((sum, po) => sum + (po.total_amount || 0), 0)

    stats.value.recentGRsCount = grs.filter(gr => {
      if (!gr.created_at) return false
      const createdDate = new Date(gr.created_at)
      const thirtyDaysAgo = new Date()
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
      return createdDate >= thirtyDaysAgo
    }).length

    stats.value.activeResourcesCount = resources.filter(r => r.status === 'Active').length

    stats.value.pendingBusinessCases = businessCases.filter(bc =>
      ['Draft', 'Submitted', 'Under Review'].includes(bc.status)
    ).length

    // Get recent items (last 5)
    recentGoodsReceipts.value = grs
      .sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
      .slice(0, 5)

    recentPurchaseOrders.value = pos
      .sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
      .slice(0, 5)

  } catch (e: any) {
    console.error('Dashboard error:', e)
    error.value = 'Failed to load dashboard data'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardData()
})

// Helpers
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount)
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

const getUtilizationPercentage = computed(() => {
  if (stats.value.totalBudget === 0) return 0
  return Math.round((stats.value.totalSpend / stats.value.totalBudget) * 100)
})

const getUtilizationColor = computed(() => {
  const pct = getUtilizationPercentage.value
  if (pct < 50) return '#10b981' // green
  if (pct < 80) return '#f59e0b' // orange
  return '#ef4444' // red
})

const isManager = computed(() => {
  return user.value && ['Admin', 'Manager'].includes(user.value.role)
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p style="color: #666; font-size: 0.95rem; margin-top: 0.25rem;">
          Welcome back, <strong>{{ user?.username }}</strong> ({{ user?.role }})
        </p>
      </div>
    </div>

    <div v-if="loading" style="text-align: center; padding: 3rem; color: #666;">
      Loading dashboard data...
    </div>

    <div v-else-if="error" style="padding: 2rem; background: #fee; border-radius: 8px; color: #c00;">
      {{ error }}
    </div>

    <div v-else>
      <!-- Statistics Cards -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
        <!-- Budget Overview -->
        <div class="stat-card">
          <div class="stat-icon" style="background-color: #e0e7ff;">
            <span style="font-size: 1.5rem;">💰</span>
          </div>
          <div class="stat-content">
            <div class="stat-label">Total Budget</div>
            <div class="stat-value">{{ formatCurrency(stats.totalBudget) }}</div>
            <div class="stat-meta">{{ budgetItems.length }} budget items</div>
          </div>
        </div>

        <!-- Spend Overview -->
        <div class="stat-card">
          <div class="stat-icon" style="background-color: #fef3c7;">
            <span style="font-size: 1.5rem;">📊</span>
          </div>
          <div class="stat-content">
            <div class="stat-label">Total Spend</div>
            <div class="stat-value">{{ formatCurrency(stats.totalSpend) }}</div>
            <div class="stat-meta" :style="{ color: getUtilizationColor }">
              {{ getUtilizationPercentage }}% of budget
            </div>
          </div>
        </div>

        <!-- Open POs -->
        <div class="stat-card">
          <div class="stat-icon" style="background-color: #dbeafe;">
            <span style="font-size: 1.5rem;">📄</span>
          </div>
          <div class="stat-content">
            <div class="stat-label">Open Purchase Orders</div>
            <div class="stat-value">{{ stats.openPOsCount }}</div>
            <div class="stat-meta">{{ formatCurrency(stats.openPOsValue) }} value</div>
          </div>
        </div>

        <!-- Active Resources -->
        <div class="stat-card">
          <div class="stat-icon" style="background-color: #d1fae5;">
            <span style="font-size: 1.5rem;">👥</span>
          </div>
          <div class="stat-content">
            <div class="stat-label">Active Resources</div>
            <div class="stat-value">{{ stats.activeResourcesCount }}</div>
            <div class="stat-meta">{{ stats.recentGRsCount }} GRs this month</div>
          </div>
        </div>

        <!-- Pending Business Cases -->
        <div class="stat-card" v-if="isManager">
          <div class="stat-icon" style="background-color: #fce7f3;">
            <span style="font-size: 1.5rem;">📋</span>
          </div>
          <div class="stat-content">
            <div class="stat-label">Pending Business Cases</div>
            <div class="stat-value">{{ stats.pendingBusinessCases }}</div>
            <div class="stat-meta">Awaiting review/approval</div>
          </div>
        </div>
      </div>

      <!-- Budget Utilization Bar -->
      <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem;">
        <h2 style="font-size: 1.1rem; margin: 0 0 1rem 0; color: #333;">Budget Utilization</h2>
        <div style="background: #f3f4f6; height: 40px; border-radius: 8px; overflow: hidden; position: relative;">
          <div
            :style="{
              width: getUtilizationPercentage + '%',
              height: '100%',
              backgroundColor: getUtilizationColor,
              transition: 'width 0.5s ease'
            }"
          ></div>
          <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; font-weight: 600; color: #333;">
            {{ formatCurrency(stats.totalSpend) }} / {{ formatCurrency(stats.totalBudget) }} ({{ getUtilizationPercentage }}%)
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem;">
        <h2 style="font-size: 1.1rem; margin: 0 0 1rem 0; color: #333;">Quick Actions</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
          <NuxtLink to="/budget-items" class="quick-action-btn">
            <span style="font-size: 1.5rem; margin-bottom: 0.5rem;">💰</span>
            <span>Manage Budgets</span>
          </NuxtLink>
          <NuxtLink to="/business-cases" class="quick-action-btn">
            <span style="font-size: 1.5rem; margin-bottom: 0.5rem;">📋</span>
            <span>Business Cases</span>
          </NuxtLink>
          <NuxtLink to="/purchase-orders" class="quick-action-btn">
            <span style="font-size: 1.5rem; margin-bottom: 0.5rem;">📄</span>
            <span>Purchase Orders</span>
          </NuxtLink>
          <NuxtLink to="/goods-receipts" class="quick-action-btn">
            <span style="font-size: 1.5rem; margin-bottom: 0.5rem;">📦</span>
            <span>Goods Receipts</span>
          </NuxtLink>
          <NuxtLink to="/resources" class="quick-action-btn" v-if="isManager">
            <span style="font-size: 1.5rem; margin-bottom: 0.5rem;">👥</span>
            <span>Resources</span>
          </NuxtLink>
          <NuxtLink to="/admin/audit" class="quick-action-btn" v-if="isManager">
            <span style="font-size: 1.5rem; margin-bottom: 0.5rem;">📊</span>
            <span>Audit Logs</span>
          </NuxtLink>
        </div>
      </div>

      <!-- Recent Activity -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem;">
        <!-- Recent Purchase Orders -->
        <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <h2 style="font-size: 1.1rem; margin: 0 0 1rem 0; color: #333;">Recent Purchase Orders</h2>
          <div v-if="recentPurchaseOrders.length === 0" style="color: #999; font-size: 0.9rem;">
            No purchase orders yet
          </div>
          <div v-else style="display: flex; flex-direction: column; gap: 0.75rem;">
            <div
              v-for="po in recentPurchaseOrders"
              :key="po.id"
              style="padding: 0.75rem; background: #f9fafb; border-radius: 6px; border-left: 3px solid #3b82f6;"
            >
              <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                  <div style="font-weight: 600; color: #333; margin-bottom: 0.25rem;">{{ po.po_number }}</div>
                  <div style="font-size: 0.85rem; color: #666;">{{ po.supplier || 'No supplier' }}</div>
                </div>
                <div style="text-align: right;">
                  <div style="font-weight: 600; color: #3b82f6;">{{ formatCurrency(po.total_amount) }}</div>
                  <div style="font-size: 0.8rem; color: #999;">{{ formatDate(po.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
          <NuxtLink to="/purchase-orders" style="display: block; margin-top: 1rem; color: #3b82f6; font-size: 0.9rem; text-decoration: none;">
            View all →
          </NuxtLink>
        </div>

        <!-- Recent Goods Receipts -->
        <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <h2 style="font-size: 1.1rem; margin: 0 0 1rem 0; color: #333;">Recent Goods Receipts</h2>
          <div v-if="recentGoodsReceipts.length === 0" style="color: #999; font-size: 0.9rem;">
            No goods receipts yet
          </div>
          <div v-else style="display: flex; flex-direction: column; gap: 0.75rem;">
            <div
              v-for="gr in recentGoodsReceipts"
              :key="gr.id"
              style="padding: 0.75rem; background: #f9fafb; border-radius: 6px; border-left: 3px solid #10b981;"
            >
              <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                  <div style="font-weight: 600; color: #333; margin-bottom: 0.25rem;">{{ gr.gr_number }}</div>
                  <div style="font-size: 0.85rem; color: #666;">{{ gr.description || 'No description' }}</div>
                </div>
                <div style="text-align: right;">
                  <div style="font-weight: 600; color: #10b981;">{{ formatCurrency(gr.amount) }}</div>
                  <div style="font-size: 0.8rem; color: #999;">{{ formatDate(gr.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
          <NuxtLink to="/goods-receipts" style="display: block; margin-top: 1rem; color: #10b981; font-size: 0.9rem; text-decoration: none;">
            View all →
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 1rem;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 0.25rem;
}

.stat-meta {
  font-size: 0.8rem;
  color: #999;
}

.quick-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  text-decoration: none;
  color: #333;
  font-weight: 500;
  transition: all 0.2s;
}

.quick-action-btn:hover {
  background: #f3f4f6;
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
