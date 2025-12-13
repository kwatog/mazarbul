<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.apiBase || config.public.apiBase
const token = useCookie('access_token')
const userInfo = useCookie('user_info')

// Parse user info to check role
const currentUser = userInfo.value ? JSON.parse(userInfo.value as string) : null

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

const fetchAuditLogs = async () => {
  try {
    loading.value = true
    const res = await useApiFetch<AuditLog[]>(`/audit-logs`)
    auditLogs.value = res
  } catch (e: any) {
    error.value = 'Failed to load audit logs'
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

const getActionColor = (action: string) => {
  switch (action) {
    case 'CREATE': return '#16a34a'
    case 'UPDATE': return '#ea580c'
    case 'DELETE': return '#dc2626'
    default: return '#64748b'
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
}

onMounted(async () => {
  await Promise.all([fetchAuditLogs(), fetchUsers()])
})
</script>

<template>
  <div>
    <div class="admin-header">
      <h1 class="page-title">Audit Logs</h1>
      <p class="page-subtitle">View all system changes and activities</p>
    </div>

    <!-- Filters -->
    <div class="filters-panel card">
      <h3 class="card-title">Filters</h3>
      
      <div class="filters-grid">
        <div class="form-group">
          <label for="tableFilter">Table</label>
          <input 
            id="tableFilter"
            v-model="filters.table_name"
            type="text" 
            placeholder="e.g. purchase_order"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label for="actionFilter">Action</label>
          <select id="actionFilter" v-model="filters.action" class="form-input">
            <option value="">All Actions</option>
            <option value="CREATE">CREATE</option>
            <option value="UPDATE">UPDATE</option>
            <option value="DELETE">DELETE</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="userFilter">User</label>
          <select id="userFilter" v-model="filters.user_id" class="form-input">
            <option :value="null">All Users</option>
            <option v-for="user in users" :key="user.id" :value="user.id">
              {{ user.full_name }} (@{{ user.username }})
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="dateFrom">Date From</label>
          <input 
            id="dateFrom"
            v-model="filters.date_from"
            type="date" 
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label for="dateTo">Date To</label>
          <input 
            id="dateTo"
            v-model="filters.date_to"
            type="date" 
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>&nbsp;</label>
          <button @click="clearFilters" class="btn-secondary">
            Clear Filters
          </button>
        </div>
      </div>
    </div>

    <p v-if="loading">Loading audit logs...</p>
    <p v-else-if="error" style="color: #dc2626;">{{ error }}</p>
    
    <!-- Results Summary -->
    <div v-else class="results-summary">
      Showing {{ filteredLogs.length }} of {{ auditLogs.length }} audit entries
    </div>
    
    <!-- Audit Logs Table -->
    <div v-if="!loading && !error" class="logs-table card">
      <div v-if="filteredLogs.length === 0" class="empty-state">
        No audit logs found matching your criteria.
      </div>
      
      <div v-else class="table-container">
        <table class="audit-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>User</th>
              <th>Action</th>
              <th>Table</th>
              <th>Record ID</th>
              <th>Changes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in filteredLogs" :key="log.id" class="audit-row">
              <td class="timestamp-cell">
                {{ formatTimestamp(log.timestamp) }}
              </td>
              
              <td class="user-cell">
                <span v-if="log.user_id">
                  {{ getUserById(log.user_id)?.full_name || 'Unknown' }}
                  <br>
                  <small>@{{ getUserById(log.user_id)?.username }}</small>
                </span>
                <span v-else class="system-user">System</span>
              </td>
              
              <td class="action-cell">
                <span 
                  class="action-badge" 
                  :style="{ backgroundColor: getActionColor(log.action), color: 'white' }"
                >
                  {{ log.action }}
                </span>
              </td>
              
              <td class="table-cell">{{ log.table_name }}</td>
              <td class="record-cell">{{ log.record_id }}</td>
              
              <td class="changes-cell">
                <div v-if="log.action === 'CREATE'" class="change-summary">
                  <strong>Created:</strong>
                  <details v-if="log.new_values">
                    <summary>View details</summary>
                    <pre class="json-preview">{{ JSON.stringify(parseJsonSafely(log.new_values), null, 2) }}</pre>
                  </details>
                </div>
                
                <div v-else-if="log.action === 'DELETE'" class="change-summary">
                  <strong>Deleted:</strong>
                  <details v-if="log.old_values">
                    <summary>View details</summary>
                    <pre class="json-preview">{{ JSON.stringify(parseJsonSafely(log.old_values), null, 2) }}</pre>
                  </details>
                </div>
                
                <div v-else-if="log.action === 'UPDATE'" class="change-summary">
                  <strong>Updated</strong>
                  <div v-if="log.old_values && log.new_values" class="update-details">
                    <details>
                      <summary>View changes</summary>
                      <div class="change-comparison">
                        <div class="change-section">
                          <h5>Before:</h5>
                          <pre class="json-preview">{{ JSON.stringify(parseJsonSafely(log.old_values), null, 2) }}</pre>
                        </div>
                        <div class="change-section">
                          <h5>After:</h5>
                          <pre class="json-preview">{{ JSON.stringify(parseJsonSafely(log.new_values), null, 2) }}</pre>
                        </div>
                      </div>
                    </details>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-header {
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  color: var(--color-muted);
  font-size: 1.1rem;
  margin-bottom: 0;
}

.filters-panel {
  margin-bottom: 1.5rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.form-input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.1);
}

.btn-secondary {
  background-color: #f1f5f9;
  color: #475569;
  border: 1px solid #cbd5e1;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.results-summary {
  margin-bottom: 1rem;
  color: var(--color-muted);
  font-size: 0.9rem;
}

.logs-table {
  overflow: hidden;
}

.table-container {
  overflow-x: auto;
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.audit-table th {
  background-color: #f8fafc;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #e2e8f0;
  white-space: nowrap;
}

.audit-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: top;
}

.audit-row:hover {
  background-color: #f8fafc;
}

.timestamp-cell {
  white-space: nowrap;
  font-family: monospace;
}

.user-cell small {
  color: var(--color-muted);
}

.system-user {
  font-style: italic;
  color: var(--color-muted);
}

.action-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.table-cell {
  font-family: monospace;
}

.record-cell {
  font-family: monospace;
  color: var(--color-muted);
}

.changes-cell {
  max-width: 300px;
}

.change-summary strong {
  color: var(--color-text);
}

.json-preview {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 0.5rem;
  font-size: 0.75rem;
  max-height: 200px;
  overflow: auto;
  margin: 0.5rem 0;
}

.change-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.change-section h5 {
  margin: 0 0 0.5rem 0;
  font-size: 0.8rem;
  color: var(--color-muted);
}

details {
  margin-top: 0.5rem;
}

summary {
  cursor: pointer;
  color: var(--color-primary);
  font-weight: 500;
}

summary:hover {
  text-decoration: underline;
}

.empty-state {
  text-align: center;
  color: var(--color-muted);
  padding: 3rem;
  font-style: italic;
}

@media (max-width: 1024px) {
  .filters-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
  
  .change-comparison {
    grid-template-columns: 1fr;
  }
}
</style>
