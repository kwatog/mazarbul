<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.apiBase || config.public.apiBase
const userInfo = useCookie('user_info')

// Parse user info to check role
const currentUser = userInfo.value ? JSON.parse(userInfo.value as string) : null

interface BudgetItem {
  id: number
  workday_ref: string
  title: string
  description?: string
  budget_amount: number
  currency: string
  fiscal_year: number
  owner_group_id: number
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

const items = ref<BudgetItem[]>([])
const groups = ref<UserGroup[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Filter state
const filterFiscalYear = ref<number | null>(null)
const filterOwnerGroup = ref<number | null>(null)

// Modal state
const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedItem = ref<BudgetItem | null>(null)

// Form state
const form = ref({
  workday_ref: '',
  title: '',
  description: '',
  budget_amount: 0,
  currency: 'USD',
  fiscal_year: new Date().getFullYear(),
  owner_group_id: 0
})

const fetchGroups = async () => {
  try {
    const res = await useApiFetch<UserGroup[]>('/user-groups')
    groups.value = res as any
  } catch (e: any) {
    console.error('Failed to load groups:', e)
  }
}

const fetchItems = async () => {
  try {
    loading.value = true
    let url = '/budget-items?limit=100'
    if (filterFiscalYear.value) {
      url += `&fiscal_year=${filterFiscalYear.value}`
    }
    if (filterOwnerGroup.value) {
      url += `&owner_group_id=${filterOwnerGroup.value}`
    }
    const res = await useApiFetch<BudgetItem[]>(url)
    items.value = res as any
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load budget items.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    workday_ref: '',
    title: '',
    description: '',
    budget_amount: 0,
    currency: 'USD',
    fiscal_year: new Date().getFullYear(),
    owner_group_id: groups.value[0]?.id || 0
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (item: BudgetItem) => {
  selectedItem.value = item
  form.value = {
    workday_ref: item.workday_ref,
    title: item.title,
    description: item.description || '',
    budget_amount: item.budget_amount,
    currency: item.currency,
    fiscal_year: item.fiscal_year,
    owner_group_id: item.owner_group_id
  }
  showEditModal.value = true
}

const closeModals = () => {
  showCreateModal.value = false
  showEditModal.value = false
  selectedItem.value = null
  resetForm()
}

const createItem = async () => {
  try {
    await useApiFetch('/budget-items', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to create budget item: ${e.data?.detail || e.message}`)
  }
}

const updateItem = async () => {
  if (!selectedItem.value) return
  try {
    await useApiFetch(`/budget-items/${selectedItem.value.id}`, {
      method: 'PUT',
      body: {
        title: form.value.title,
        description: form.value.description,
        budget_amount: form.value.budget_amount,
        currency: form.value.currency,
        fiscal_year: form.value.fiscal_year
      }
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to update budget item: ${e.data?.detail || e.message}`)
  }
}

const deleteItem = async (item: BudgetItem) => {
  if (!confirm(`Are you sure you want to delete budget item "${item.title}"?`)) {
    return
  }
  try {
    await useApiFetch(`/budget-items/${item.id}`, {
      method: 'DELETE'
    })
    await fetchItems()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to delete budget item: ${e.data?.detail || e.message}`)
  }
}

const canEdit = (item: BudgetItem) => {
  if (!currentUser) return false
  if (['Admin', 'Manager'].includes(currentUser.role)) return true
  return item.created_by === currentUser.id
}

const canDelete = () => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
}

const formatCurrency = (amount: number, currency: string) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(amount)
}

onMounted(async () => {
  await fetchGroups()
  await fetchItems()
})
</script>

<template>
  <section class="card">
    <div class="header-row">
      <div>
        <h1 class="card-title">Budget Items</h1>
        <p class="card-sub">Manage budget allocations from Workday</p>
      </div>
      <button @click="openCreateModal" class="btn-primary">
        + Create Budget Item
      </button>
    </div>

    <!-- Filters -->
    <div class="filters">
      <div class="filter-group">
        <label>Fiscal Year:</label>
        <select v-model="filterFiscalYear" @change="fetchItems">
          <option :value="null">All Years</option>
          <option :value="2024">2024</option>
          <option :value="2025">2025</option>
          <option :value="2026">2026</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Owner Group:</label>
        <select v-model="filterOwnerGroup" @change="fetchItems">
          <option :value="null">All Groups</option>
          <option v-for="group in groups" :key="group.id" :value="group.id">
            {{ group.name }}
          </option>
        </select>
      </div>
    </div>

    <p v-if="loading">Loading…</p>
    <p v-else-if="error" style="color: #cc0000;">{{ error }}</p>
    <div v-else-if="items.length === 0" class="empty-state">
      No budget items found. Click "Create Budget Item" to add one.
    </div>
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>Workday Ref</th>
          <th>Title</th>
          <th>Budget Amount</th>
          <th>Fiscal Year</th>
          <th>Owner Group</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td><code>{{ item.workday_ref }}</code></td>
          <td>
            <strong>{{ item.title }}</strong>
            <div v-if="item.description" class="description">{{ item.description }}</div>
          </td>
          <td>{{ formatCurrency(item.budget_amount, item.currency) }}</td>
          <td>{{ item.fiscal_year }}</td>
          <td>
            <span class="badge">
              {{ groups.find(g => g.id === item.owner_group_id)?.name || 'Unknown' }}
            </span>
          </td>
          <td>
            <div class="action-buttons">
              <button
                v-if="canEdit(item)"
                @click="openEditModal(item)"
                class="btn-small btn-edit"
                title="Edit"
              >
                ✏️ Edit
              </button>
              <button
                v-if="canDelete()"
                @click="deleteItem(item)"
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
        <h2>Create Budget Item</h2>
        <form @submit.prevent="createItem">
          <div class="form-group">
            <label>Workday Reference <span class="required">*</span></label>
            <input
              v-model="form.workday_ref"
              type="text"
              placeholder="e.g., WD-2025-FIN-001"
              required
            />
          </div>

          <div class="form-group">
            <label>Title <span class="required">*</span></label>
            <input
              v-model="form.title"
              type="text"
              placeholder="e.g., Cloud Infrastructure Budget 2025"
              required
            />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="form.description"
              rows="3"
              placeholder="Optional description"
            ></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Budget Amount <span class="required">*</span></label>
              <input
                v-model.number="form.budget_amount"
                type="number"
                step="0.01"
                min="0"
                required
              />
            </div>

            <div class="form-group">
              <label>Currency <span class="required">*</span></label>
              <select v-model="form.currency" required>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Fiscal Year <span class="required">*</span></label>
            <input
              v-model.number="form.fiscal_year"
              type="number"
              min="2020"
              max="2030"
              required
            />
          </div>

          <div class="form-group">
            <label>Owner Group <span class="required">*</span></label>
            <select v-model.number="form.owner_group_id" required>
              <option v-for="group in groups" :key="group.id" :value="group.id">
                {{ group.name }}
              </option>
            </select>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModals" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary">
              Create Budget Item
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <h2>Edit Budget Item</h2>
        <form @submit.prevent="updateItem">
          <div class="form-group">
            <label>Workday Reference</label>
            <input
              v-model="form.workday_ref"
              type="text"
              disabled
              class="disabled-input"
            />
            <small>Workday reference cannot be changed</small>
          </div>

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
              rows="3"
            ></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Budget Amount <span class="required">*</span></label>
              <input
                v-model.number="form.budget_amount"
                type="number"
                step="0.01"
                min="0"
                required
              />
            </div>

            <div class="form-group">
              <label>Currency <span class="required">*</span></label>
              <select v-model="form.currency" required>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Fiscal Year <span class="required">*</span></label>
            <input
              v-model.number="form.fiscal_year"
              type="number"
              min="2020"
              max="2030"
              required
            />
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

.filter-group select {
  padding: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background-color: white;
  font-size: 0.9rem;
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
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background-color: var(--color-primary);
  color: white;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
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
  max-width: 600px;
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

.disabled-input {
  background-color: var(--color-background-soft);
  cursor: not-allowed;
}

.form-group small {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
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
