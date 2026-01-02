<script setup lang="ts">
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
    stats.value.totalBudget = budgetItems.value.reduce((sum, item) => sum + (parseFloat(item.budget_amount) || 0), 0)

    const openPOs = pos.filter(po => ['Open', 'Approved', 'In Progress'].includes(po.status))
    stats.value.openPOsCount = openPOs.length
    stats.value.openPOsValue = openPOs.reduce((sum, po) => sum + (parseFloat(po.total_amount) || 0), 0)

    stats.value.totalSpend = pos.reduce((sum, po) => sum + (parseFloat(po.total_amount) || 0), 0)

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
const formatCurrency = (amount: string | number) => {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(num)
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
  if (pct < 50) return 'var(--color-success)'
  if (pct < 80) return 'var(--color-warning)'
  return 'var(--color-error)'
})

const isManager = computed(() => {
  return user.value && ['Admin', 'Manager'].includes(user.value.role)
})
</script>

<template>
  <div class="main-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">
          Welcome back, <strong>{{ user?.username }}</strong> ({{ user?.role }})
        </p>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <LoadingSpinner size="lg" label="Loading dashboard data..." />
      <p class="text-muted">Loading dashboard data...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <p class="error-text">{{ error }}</p>
    </div>

    <div v-else>
      <!-- Statistics Cards -->
      <div class="stats-grid">
        <!-- Budget Overview -->
        <BaseCard padding="md" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-icon stat-icon-primary">
              <span>💰</span>
            </div>
            <div class="stat-details">
              <div class="stat-label">Total Budget</div>
              <div class="stat-value">{{ formatCurrency(stats.totalBudget) }}</div>
              <div class="stat-meta">{{ budgetItems.length }} budget items</div>
            </div>
          </div>
        </BaseCard>

        <!-- Spend Overview -->
        <BaseCard padding="md" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-icon stat-icon-warning">
              <span>📊</span>
            </div>
            <div class="stat-details">
              <div class="stat-label">Total Spend</div>
              <div class="stat-value">{{ formatCurrency(stats.totalSpend) }}</div>
              <div class="stat-meta" :style="{ color: getUtilizationColor }">
                {{ getUtilizationPercentage }}% of budget
              </div>
            </div>
          </div>
        </BaseCard>

        <!-- Open POs -->
        <BaseCard padding="md" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-icon stat-icon-info">
              <span>📄</span>
            </div>
            <div class="stat-details">
              <div class="stat-label">Open Purchase Orders</div>
              <div class="stat-value">{{ stats.openPOsCount }}</div>
              <div class="stat-meta">{{ formatCurrency(stats.openPOsValue) }} value</div>
            </div>
          </div>
        </BaseCard>

        <!-- Active Resources -->
        <BaseCard padding="md" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-icon stat-icon-success">
              <span>👥</span>
            </div>
            <div class="stat-details">
              <div class="stat-label">Active Resources</div>
              <div class="stat-value">{{ stats.activeResourcesCount }}</div>
              <div class="stat-meta">{{ stats.recentGRsCount }} GRs this month</div>
            </div>
          </div>
        </BaseCard>

        <!-- Pending Business Cases -->
        <BaseCard v-if="isManager" padding="md" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-icon stat-icon-secondary">
              <span>📋</span>
            </div>
            <div class="stat-details">
              <div class="stat-label">Pending Business Cases</div>
              <div class="stat-value">{{ stats.pendingBusinessCases }}</div>
              <div class="stat-meta">Awaiting review/approval</div>
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- Budget Utilization Bar -->
      <BaseCard title="Budget Utilization" padding="md">
        <div class="utilization-bar-container">
          <div class="utilization-bar-bg">
            <div
              class="utilization-bar-fill"
              :style="{
                width: getUtilizationPercentage + '%',
                backgroundColor: getUtilizationColor
              }"
            ></div>
            <div class="utilization-bar-label">
              {{ formatCurrency(stats.totalSpend) }} / {{ formatCurrency(stats.totalBudget) }} ({{ getUtilizationPercentage }}%)
            </div>
          </div>
        </div>
      </BaseCard>

      <!-- Quick Actions -->
      <BaseCard title="Quick Actions" padding="md">
        <div class="quick-actions-grid">
          <NuxtLink to="/budget-items" class="quick-action-btn">
            <span class="quick-action-icon">💰</span>
            <span>Manage Budgets</span>
          </NuxtLink>
          <NuxtLink to="/business-cases" class="quick-action-btn">
            <span class="quick-action-icon">📋</span>
            <span>Business Cases</span>
          </NuxtLink>
          <NuxtLink to="/purchase-orders" class="quick-action-btn">
            <span class="quick-action-icon">📄</span>
            <span>Purchase Orders</span>
          </NuxtLink>
          <NuxtLink to="/goods-receipts" class="quick-action-btn">
            <span class="quick-action-icon">📦</span>
            <span>Goods Receipts</span>
          </NuxtLink>
          <NuxtLink v-if="isManager" to="/resources" class="quick-action-btn">
            <span class="quick-action-icon">👥</span>
            <span>Resources</span>
          </NuxtLink>
          <NuxtLink v-if="isManager" to="/admin/audit" class="quick-action-btn">
            <span class="quick-action-icon">📊</span>
            <span>Audit Logs</span>
          </NuxtLink>
        </div>
      </BaseCard>

      <!-- Recent Activity -->
      <div class="recent-activity-grid">
        <!-- Recent Purchase Orders -->
        <BaseCard title="Recent Purchase Orders" padding="md">
          <EmptyState
            v-if="recentPurchaseOrders.length === 0"
            title="No purchase orders yet"
            description="Purchase orders will appear here once created"
          />
          <div v-else class="recent-items-list">
            <div
              v-for="po in recentPurchaseOrders"
              :key="po.id"
              class="recent-item recent-item-info"
            >
              <div class="recent-item-content">
                <div class="recent-item-title">{{ po.po_number }}</div>
                <div class="recent-item-subtitle">{{ po.supplier || 'No supplier' }}</div>
              </div>
              <div class="recent-item-meta">
                <div class="recent-item-amount recent-item-amount-info">{{ formatCurrency(po.total_amount) }}</div>
                <div class="recent-item-date">{{ formatDate(po.created_at) }}</div>
              </div>
            </div>
          </div>
          <template #footer>
            <NuxtLink to="/purchase-orders" class="view-all-link">
              View all →
            </NuxtLink>
          </template>
        </BaseCard>

        <!-- Recent Goods Receipts -->
        <BaseCard title="Recent Goods Receipts" padding="md">
          <EmptyState
            v-if="recentGoodsReceipts.length === 0"
            title="No goods receipts yet"
            description="Goods receipts will appear here once created"
          />
          <div v-else class="recent-items-list">
            <div
              v-for="gr in recentGoodsReceipts"
              :key="gr.id"
              class="recent-item recent-item-success"
            >
              <div class="recent-item-content">
                <div class="recent-item-title">{{ gr.gr_number }}</div>
                <div class="recent-item-subtitle">{{ gr.description || 'No description' }}</div>
              </div>
              <div class="recent-item-meta">
                <div class="recent-item-amount recent-item-amount-success">{{ formatCurrency(gr.amount) }}</div>
                <div class="recent-item-date">{{ formatDate(gr.created_at) }}</div>
              </div>
            </div>
          </div>
          <template #footer>
            <NuxtLink to="/goods-receipts" class="view-all-link">
              View all →
            </NuxtLink>
          </template>
        </BaseCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  gap: var(--spacing-4);
}

.error-container {
  padding: var(--spacing-6);
  background: #fee;
  border-radius: var(--radius-lg);
}

.error-text {
  color: var(--color-error);
  margin: 0;
}

/* Statistics Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.stat-card-content {
  display: flex;
  gap: var(--spacing-4);
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: var(--text-2xl);
}

.stat-icon-primary {
  background: #e0e7ff;
}

.stat-icon-warning {
  background: #fef3c7;
}

.stat-icon-info {
  background: #dbeafe;
}

.stat-icon-success {
  background: #d1fae5;
}

.stat-icon-secondary {
  background: #fce7f3;
}

.stat-details {
  flex: 1;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-gray-600);
  margin-bottom: var(--spacing-1);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-gray-900);
  margin-bottom: var(--spacing-1);
}

.stat-meta {
  font-size: var(--text-xs);
  color: var(--color-gray-500);
}

/* Utilization Bar */
.utilization-bar-container {
  margin-top: var(--spacing-4);
}

.utilization-bar-bg {
  background: var(--color-gray-100);
  height: 40px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  position: relative;
}

.utilization-bar-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.utilization-bar-label {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--color-gray-900);
  font-size: var(--text-sm);
}

/* Quick Actions */
.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--spacing-4);
  margin-top: var(--spacing-4);
}

.quick-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-4) var(--spacing-3);
  background: var(--color-gray-50);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: var(--color-gray-900);
  font-weight: 500;
  transition: all var(--transition-fast);
  gap: var(--spacing-2);
}

.quick-action-btn:hover {
  background: var(--color-gray-100);
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.quick-action-icon {
  font-size: var(--text-2xl);
}

/* Recent Activity */
.recent-activity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: var(--spacing-4);
}

.recent-items-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: start;
  padding: var(--spacing-3);
  background: var(--color-gray-50);
  border-radius: var(--radius-md);
  border-left: 3px solid;
}

.recent-item-info {
  border-left-color: var(--color-info);
}

.recent-item-success {
  border-left-color: var(--color-success);
}

.recent-item-content {
  flex: 1;
}

.recent-item-title {
  font-weight: 600;
  color: var(--color-gray-900);
  margin-bottom: var(--spacing-1);
  font-size: var(--text-sm);
}

.recent-item-subtitle {
  font-size: var(--text-sm);
  color: var(--color-gray-600);
}

.recent-item-meta {
  text-align: right;
}

.recent-item-amount {
  font-weight: 600;
  margin-bottom: var(--spacing-1);
  font-size: var(--text-sm);
}

.recent-item-amount-info {
  color: var(--color-info);
}

.recent-item-amount-success {
  color: var(--color-success);
}

.recent-item-date {
  font-size: var(--text-xs);
  color: var(--color-gray-500);
}

.view-all-link {
  display: block;
  color: var(--color-primary);
  font-size: var(--text-sm);
  text-decoration: none;
  font-weight: 500;
}

.view-all-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .quick-actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .recent-activity-grid {
    grid-template-columns: 1fr;
  }
}
</style>
