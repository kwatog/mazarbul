<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.apiBase || config.public.apiBase
const userInfo = useCookie('user_info')

const currentUser = userInfo.value ? JSON.parse(userInfo.value as string) : null

interface BusinessCase {
  id: number
  title: string
  description?: string
  requestor?: string
  dept?: string
  lead_group_id?: number
  estimated_cost?: number
  status?: string
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface UserGroup {
  id: number
  name: string
  description?: string
}

const cases = ref<BusinessCase[]>([])
const groups = ref<UserGroup[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Filter state
const filterStatus = ref<string | null>(null)
const filterRequestor = ref<string>('')

// Modal state
const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedCase = ref<BusinessCase | null>(null)

// Form state
const form = ref({
  title: '',
  description: '',
  requestor: '',
  dept: '',
  lead_group_id: null as number | null,
  estimated_cost: 0,
  status: 'Draft'
})

const statuses = ['Draft', 'Submitted', 'Under Review', 'Approved', 'Rejected', 'Completed']

const fetchGroups = async () => {
  try {
    const res = await useApiFetch<UserGroup[]>('/user-groups')
    groups.value = res as any
  } catch (e: any) {
    console.error('Failed to load groups:', e)
  }
}

const fetchCases = async () => {
  try {
    loading.value = true
    let url = '/business-cases?limit=100'
    if (filterStatus.value) {
      url += `&status=${filterStatus.value}`
    }
    if (filterRequestor.value) {
      url += `&requestor=${filterRequestor.value}`
    }
    const res = await useApiFetch<BusinessCase[]>(url)
    cases.value = res as any
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load business cases.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    title: '',
    description: '',
    requestor: currentUser?.full_name || '',
    dept: currentUser?.department || '',
    lead_group_id: null,
    estimated_cost: 0,
    status: 'Draft'
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (bc: BusinessCase) => {
  selectedCase.value = bc
  form.value = {
    title: bc.title,
    description: bc.description || '',
    requestor: bc.requestor || '',
    dept: bc.dept || '',
    lead_group_id: bc.lead_group_id || null,
    estimated_cost: bc.estimated_cost || 0,
    status: bc.status || 'Draft'
  }
  showEditModal.value = true
}

const closeModals = () => {
  showCreateModal.value = false
  showEditModal.value = false
  selectedCase.value = null
  resetForm()
}

const createCase = async () => {
  try {
    await useApiFetch('/business-cases', {
      method: 'POST',
      body: form.value
    })
    await fetchCases()
    closeModals()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to create business case: ${e.data?.detail || e.message}`)
  }
}

const updateCase = async () => {
  if (!selectedCase.value) return
  try {
    await useApiFetch(`/business-cases/${selectedCase.value.id}`, {
      method: 'PUT',
      body: form.value
    })
    await fetchCases()
    closeModals()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to update business case: ${e.data?.detail || e.message}`)
  }
}

const deleteCase = async (bc: BusinessCase) => {
  if (!confirm(`Are you sure you want to delete business case "${bc.title}"?`)) {
    return
  }
  try {
    await useApiFetch(`/business-cases/${bc.id}`, {
      method: 'DELETE'
    })
    await fetchCases()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to delete business case: ${e.data?.detail || e.message}`)
  }
}

const canEdit = (bc: BusinessCase) => {
  if (!currentUser) return false
  if (['Admin', 'Manager'].includes(currentUser.role)) return true
  return bc.created_by === currentUser.id
}

const canDelete = () => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
}

const getStatusColor = (status?: string) => {
  const colors: Record<string, string> = {
    'Draft': '#6b7280',
    'Submitted': '#3b82f6',
    'Under Review': '#f59e0b',
    'Approved': '#10b981',
    'Rejected': '#ef4444',
    'Completed': '#8b5cf6'
  }
  return colors[status || 'Draft'] || '#6b7280'
}

onMounted(async () => {
  await fetchGroups()
  await fetchCases()
})
</script>

<template>
  <section class="card">
    <div class="header-row">
      <div>
        <h1 class="card-title">Business Cases</h1>
        <p class="card-sub">Track business case requests and approvals</p>
      </div>
      <button @click="openCreateModal" class="btn-primary">
        + Create Business Case
      </button>
    </div>

    <!-- Filters -->
    <div class="filters">
      <div class="filter-group">
        <label>Status:</label>
        <select v-model="filterStatus" @change="fetchCases">
          <option :value="null">All Statuses</option>
          <option v-for="status in statuses" :key="status" :value="status">
            {{ status }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label>Requestor:</label>
        <input
          v-model="filterRequestor"
          type="text"
          placeholder="Filter by name..."
          @input="fetchCases"
        />
      </div>
    </div>

    <p v-if="loading">Loading…</p>
    <p v-else-if="error" style="color: #cc0000;">{{ error }}</p>
    <div v-else-if="cases.length === 0" class="empty-state">
      No business cases found. Click "Create Business Case" to add one.
    </div>
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>Title</th>
          <th>Requestor</th>
          <th>Department</th>
          <th>Lead Group</th>
          <th>Estimated Cost</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="bc in cases" :key="bc.id">
          <td>
            <strong>{{ bc.title }}</strong>
            <div v-if="bc.description" class="description">{{ bc.description }}</div>
          </td>
          <td>{{ bc.requestor || '-' }}</td>
          <td>{{ bc.dept || '-' }}</td>
          <td>
            <span v-if="bc.lead_group_id" class="badge badge-group">
              {{ groups.find(g => g.id === bc.lead_group_id)?.name || 'Unknown' }}
            </span>
            <span v-else class="text-muted">-</span>
          </td>
          <td>
            <span v-if="bc.estimated_cost" class="amount">
              ${{ bc.estimated_cost.toLocaleString() }}
            </span>
            <span v-else class="text-muted">-</span>
          </td>
          <td>
            <span
              class="badge badge-status"
              :style="{ backgroundColor: getStatusColor(bc.status) }"
            >
              {{ bc.status || 'Draft' }}
            </span>
          </td>
          <td>
            <div class="action-buttons">
              <button
                v-if="canEdit(bc)"
                @click="openEditModal(bc)"
                class="btn-small btn-edit"
                title="Edit"
              >
                ✏️ Edit
              </button>
              <button
                v-if="canDelete()"
                @click="deleteCase(bc)"
                class="btn-small btn-delete"
                title="Delete"
              >
                🗑️ Delete
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <h2>Create Business Case</h2>
        <form @submit.prevent="createCase">
          <div class="form-group">
            <label>Title <span class="required">*</span></label>
            <input
              v-model="form.title"
              type="text"
              placeholder="e.g., Cloud Migration Project"
              required
            />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="form.description"
              rows="4"
              placeholder="Detailed description of the business case..."
            ></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Requestor <span class="required">*</span></label>
              <input
                v-model="form.requestor"
                type="text"
                placeholder="Name"
                required
              />
            </div>

            <div class="form-group">
              <label>Department <span class="required">*</span></label>
              <input
                v-model="form.dept"
                type="text"
                placeholder="Department"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label>Lead Group</label>
            <select v-model.number="form.lead_group_id">
              <option :value="null">No lead group</option>
              <option v-for="group in groups" :key="group.id" :value="group.id">
                {{ group.name }}
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Estimated Cost (USD)</label>
              <input
                v-model.number="form.estimated_cost"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
              />
            </div>

            <div class="form-group">
              <label>Status <span class="required">*</span></label>
              <select v-model="form.status" required>
                <option v-for="status in statuses" :key="status" :value="status">
                  {{ status }}
                </option>
              </select>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModals" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary">
              Create Business Case
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <h2>Edit Business Case</h2>
        <form @submit.prevent="updateCase">
          <div class="form-group">
            <label>Title <span class="required">*</span></label>
            <input
              v-model="form.title"
              type="text"
              required
            />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="form.description"
              rows="4"
            ></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Requestor <span class="required">*</span></label>
              <input
                v-model="form.requestor"
                type="text"
                required
              />
            </div>

            <div class="form-group">
              <label>Department <span class="required">*</span></label>
              <input
                v-model="form.dept"
                type="text"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label>Lead Group</label>
            <select v-model.number="form.lead_group_id">
              <option :value="null">No lead group</option>
              <option v-for="group in groups" :key="group.id" :value="group.id">
                {{ group.name }}
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Estimated Cost (USD)</label>
              <input
                v-model.number="form.estimated_cost"
                type="number"
                step="0.01"
                min="0"
              />
            </div>

            <div class="form-group">
              <label>Status <span class="required">*</span></label>
              <select v-model="form.status" required>
                <option v-for="status in statuses" :key="status" :value="status">
                  {{ status }}
                </option>
              </select>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModals" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary">
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: var(--color-background-soft);
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
}

.filter-group select,
.filter-group input {
  padding: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background-color: white;
  font-size: 0.9rem;
}

.filter-group input {
  width: 200px;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-muted);
  background-color: var(--color-background-soft);
  border-radius: 8px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.data-table th {
  text-align: left;
  padding: 0.75rem;
  background-color: var(--color-background-soft);
  font-weight: 600;
  border-bottom: 2px solid var(--color-border);
}

.data-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  vertical-align: middle;
}

.data-table tbody tr:hover {
  background-color: var(--color-background-soft);
}

.description {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-top: 0.25rem;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-muted {
  color: var(--color-text-muted);
}

.amount {
  font-weight: 600;
  color: #10b981;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.badge-group {
  background-color: var(--color-primary);
  color: white;
}

.badge-status {
  color: white;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #17c653;
}

.btn-secondary {
  background-color: var(--color-background-soft);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background-color: var(--color-border);
}

.btn-small {
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  border: none;
  transition: all 0.2s;
}

.btn-edit {
  background-color: #3b82f6;
  color: white;
}

.btn-edit:hover {
  background-color: #2563eb;
}

.btn-delete {
  background-color: #ef4444;
  color: white;
}

.btn-delete:hover {
  background-color: #dc2626;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
}

.modal {
  background-color: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: var(--color-heading);
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 0.9rem;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(26, 188, 96, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.required {
  color: #ef4444;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}
</style>
