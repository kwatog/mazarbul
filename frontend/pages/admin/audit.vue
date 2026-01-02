<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const userInfo = useCookie('user_info')
const { success, error: showError } = useToast()

const decodeUserInfo = (value: string | null | object): any => {
  if (!value) return null
  if (typeof value === 'object') return value
  try {
    let b64 = String(value)
    if (b64.startsWith('"') && b64.endsWith('"')) {
      b64 = b64.slice(1, -1)
    }
    const json = decodeURIComponent(escape(atob(b64)))
    return JSON.parse(json)
  } catch {
    return null
  }
}

const currentUser = decodeUserInfo(userInfo.value)

// Redirect if not Manager or Admin
if (!currentUser || !['Manager', 'Admin'].includes(currentUser.role)) {
  await navigateTo('/')
}

interface AuditLog {
  id: number
  table_name: string
  record_id: number
  action: string
  old_values?: string
  new_values?: string
  user_id?: number
  timestamp: string
  ip_address?: string
}

interface User {
  id: number
  username: string
  full_name: string
}

const auditLogs = ref<AuditLog[]>([])
const users = ref<User[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Filters
const filters = ref({
  table_name: '',
  action: '',
  user_id: null as number | null,
  date_from: '',
  date_to: ''
})

const actionOptions = [
  { value: '', label: 'All Actions' },
  { value: 'CREATE', label: 'CREATE' },
  { value: 'UPDATE', label: 'UPDATE' },
  { value: 'DELETE', label: 'DELETE' }
]

const userOptions = computed(() => [
  { value: null, label: 'All Users' },
  ...users.value.map(user => ({
    value: user.id,
    label: `${user.full_name} (@${user.username})`
  }))
])

const fetchAuditLogs = async () => {
  try {
    loading.value = true
    const res = await useApiFetch<AuditLog[]>(`/audit-logs`)
    auditLogs.value = res
    error.value = null
  } catch (e: any) {
    error.value = 'Failed to load audit logs'
    showError('Failed to load audit logs')
    if (e.response?.status === 401) await navigateTo('/login')
  } finally {
    loading.value = false
  }
}

const fetchUsers = async () => {
  try {
    const res = await useApiFetch<User[]>(`/users`)
    users.value = res
  } catch (e: any) {
    console.error('Failed to load users:', e)
  }
}

const getUserById = (userId: number) => {
  return users.value.find(u => u.id === userId)
}

const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

const getActionVariant = (action: string): 'success' | 'warning' | 'danger' | 'secondary' => {
  switch (action) {
    case 'CREATE': return 'success'
    case 'UPDATE': return 'warning'
    case 'DELETE': return 'danger'
    default: return 'secondary'
  }
}

const parseJsonSafely = (jsonString?: string) => {
  if (!jsonString) return null
  try {
    return JSON.parse(jsonString)
  } catch {
    return null
  }
}

const filteredLogs = computed(() => {
  let filtered = [...auditLogs.value]

  if (filters.value.table_name) {
    filtered = filtered.filter(log =>
      log.table_name.toLowerCase().includes(filters.value.table_name.toLowerCase())
    )
  }

  if (filters.value.action) {
    filtered = filtered.filter(log => log.action === filters.value.action)
  }

  if (filters.value.user_id) {
    filtered = filtered.filter(log => log.user_id === filters.value.user_id)
  }

  if (filters.value.date_from) {
    const fromDate = new Date(filters.value.date_from)
    filtered = filtered.filter(log => new Date(log.timestamp) >= fromDate)
  }

  if (filters.value.date_to) {
    const toDate = new Date(filters.value.date_to)
    toDate.setHours(23, 59, 59) // End of day
    filtered = filtered.filter(log => new Date(log.timestamp) <= toDate)
  }

  return filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
})

const clearFilters = () => {
  filters.value = {
    table_name: '',
    action: '',
    user_id: null,
    date_from: '',
    date_to: ''
  }
  success('Filters cleared')
}

const tableColumns = [
  { key: 'timestamp', label: 'Timestamp', sortable: true },
  { key: 'user', label: 'User', sortable: false },
  { key: 'action', label: 'Action', sortable: true, align: 'center' as const },
  { key: 'table_name', label: 'Table', sortable: true },
  { key: 'record_id', label: 'Record ID', sortable: true, align: 'center' as const },
  { key: 'changes', label: 'Changes', sortable: false }
]

onMounted(async () => {
  await Promise.all([fetchAuditLogs(), fetchUsers()])
})
</script>

<template>
  <BaseCard
    title="Audit Logs"
    subtitle="View all system changes and activities"
  >
    <!-- Filters Panel -->
    <div class="filters-section" role="search" aria-label="Audit log filters">
      <div class="filters-grid">
        <BaseInput
          v-model="filters.table_name"
          label="Table Name"
          placeholder="e.g. purchase_order"
          aria-label="Filter by table name"
        />

        <BaseSelect
          v-model="filters.action"
          :options="actionOptions"
          label="Action"
          aria-label="Filter by action type"
        />

        <BaseSelect
          v-model="filters.user_id"
          :options="userOptions"
          label="User"
          aria-label="Filter by user"
        />

        <BaseInput
          v-model="filters.date_from"
          label="Date From"
          type="date"
          aria-label="Filter by start date"
        />

        <BaseInput
          v-model="filters.date_to"
          label="Date To"
          type="date"
          aria-label="Filter by end date"
        />

        <div class="filter-actions">
          <BaseButton
            variant="secondary"
            @click="clearFilters"
            aria-label="Clear all filters"
          >
            Clear Filters
          </BaseButton>
        </div>
      </div>
    </div>

    <!-- Results Summary -->
    <div v-if="!loading && !error" class="results-summary" role="status" aria-live="polite">
      Showing {{ filteredLogs.length }} of {{ auditLogs.length }} audit entries
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" label="Loading audit logs..." />
    </div>

    <!-- Error State -->
    <p v-else-if="error" class="error-message" role="alert">{{ error }}</p>

    <!-- Empty State -->
    <EmptyState
      v-else-if="filteredLogs.length === 0"
      title="No audit logs found"
      description="No audit logs match your current filter criteria. Try adjusting the filters above."
      action-text="Clear Filters"
      @action="clearFilters"
    />

    <!-- Audit Logs Table -->
    <BaseTable
      v-else
      :columns="tableColumns"
      :data="filteredLogs"
      :loading="loading"
      sticky-header
      empty-message="No audit logs found"
    >
      <template #cell-timestamp="{ value }">
        <code class="timestamp-code">{{ formatTimestamp(value) }}</code>
      </template>

      <template #cell-user="{ row }">
        <div v-if="row.user_id" class="user-info">
          <div class="user-name">{{ getUserById(row.user_id)?.full_name || 'Unknown' }}</div>
          <div class="user-username">@{{ getUserById(row.user_id)?.username }}</div>
        </div>
        <span v-else class="system-user">System</span>
      </template>

      <template #cell-action="{ value }">
        <BaseBadge :variant="getActionVariant(value)" size="sm">
          {{ value }}
        </BaseBadge>
      </template>

      <template #cell-table_name="{ value }">
        <code class="table-code">{{ value }}</code>
      </template>

      <template #cell-record_id="{ value }">
        <code class="record-code">{{ value }}</code>
      </template>

      <template #cell-changes="{ row }">
        <div class="changes-cell">
          <!-- CREATE Action -->
          <div v-if="row.action === 'CREATE'" class="change-summary">
            <strong class="change-label">Created:</strong>
            <details v-if="row.new_values" class="change-details">
              <summary class="change-toggle">View details</summary>
              <pre class="json-preview" role="region" aria-label="Created record data">{{ JSON.stringify(parseJsonSafely(row.new_values), null, 2) }}</pre>
            </details>
          </div>

          <!-- DELETE Action -->
          <div v-else-if="row.action === 'DELETE'" class="change-summary">
            <strong class="change-label">Deleted:</strong>
            <details v-if="row.old_values" class="change-details">
              <summary class="change-toggle">View details</summary>
              <pre class="json-preview" role="region" aria-label="Deleted record data">{{ JSON.stringify(parseJsonSafely(row.old_values), null, 2) }}</pre>
            </details>
          </div>

          <!-- UPDATE Action -->
          <div v-else-if="row.action === 'UPDATE'" class="change-summary">
            <strong class="change-label">Updated</strong>
            <div v-if="row.old_values && row.new_values" class="update-details">
              <details class="change-details">
                <summary class="change-toggle">View changes</summary>
                <div class="change-comparison" role="region" aria-label="Before and after comparison">
                  <div class="change-section">
                    <h5 class="change-section-title">Before:</h5>
                    <pre class="json-preview">{{ JSON.stringify(parseJsonSafely(row.old_values), null, 2) }}</pre>
                  </div>
                  <div class="change-section">
                    <h5 class="change-section-title">After:</h5>
                    <pre class="json-preview">{{ JSON.stringify(parseJsonSafely(row.new_values), null, 2) }}</pre>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </div>
      </template>
    </BaseTable>
  </BaseCard>
</template>

<style scoped>
/* Filters Section */
.filters-section {
  padding: var(--spacing-6);
  background: var(--color-gray-50);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-6);
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-4);
}

.filter-actions {
  display: flex;
  align-items: flex-end;
}

/* Results Summary */
.results-summary {
  margin-bottom: var(--spacing-4);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  padding: var(--spacing-3);
  background: var(--color-gray-50);
  border-radius: var(--radius-md);
}

/* Loading & Error States */
.loading-state {
  display: flex;
  justify-content: center;
  padding: var(--spacing-12);
}

.error-message {
  color: var(--color-error);
  padding: var(--spacing-6);
  text-align: center;
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-error);
}

/* Table Cell Styling */
.timestamp-code {
  font-family: monospace;
  background: var(--color-gray-100);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  white-space: nowrap;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.user-name {
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.user-username {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.system-user {
  font-style: italic;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.table-code,
.record-code {
  font-family: monospace;
  background: var(--color-gray-100);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

.record-code {
  color: var(--color-text-muted);
}

/* Changes Cell */
.changes-cell {
  max-width: 400px;
}

.change-summary {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.change-label {
  color: var(--color-text);
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
}

.change-details {
  margin-top: var(--spacing-2);
}

.change-toggle {
  cursor: pointer;
  color: var(--color-primary);
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
  padding: var(--spacing-2) 0;
  user-select: none;
  transition: color var(--transition-fast);
}

.change-toggle:hover {
  color: var(--color-primary-dark);
  text-decoration: underline;
}

.change-toggle:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

.json-preview {
  background-color: var(--color-gray-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  font-size: var(--text-xs);
  font-family: monospace;
  max-height: 300px;
  overflow: auto;
  margin-top: var(--spacing-2);
  line-height: 1.5;
  color: var(--color-text);
}

.change-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
  margin-top: var(--spacing-3);
}

.change-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.change-section-title {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text-light);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .filters-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }

  .change-comparison {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .filters-section {
    padding: var(--spacing-4);
  }

  .filters-grid {
    grid-template-columns: 1fr;
  }

  .changes-cell {
    max-width: 100%;
  }
}
</style>
