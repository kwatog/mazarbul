<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.apiBase || config.public.apiBase
const userInfo = useCookie('user_info')

const currentUser = userInfo.value ? JSON.parse(userInfo.value as string) : null

interface LineItem {
  id: number
  business_case_id: number
  budget_item_id: number
  owner_group_id: number
  title: string
  description?: string
  spend_category: string
  requested_amount: number
  currency: string
  planned_commit_date?: string
  status?: string
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface BusinessCase {
  id: number
  title: string
}

interface BudgetItem {
  id: number
  workday_ref: string
  title: string
}

interface UserGroup {
  id: number
  name: string
}

const items = ref<LineItem[]>([])
const businessCases = ref<BusinessCase[]>([])
const budgetItems = ref<BudgetItem[]>([])
const groups = ref<UserGroup[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Filter state
const filterBusinessCase = ref<number | null>(null)
const filterSpendCategory = ref<string | null>(null)

// Modal state
const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedItem = ref<LineItem | null>(null)

// Form state
const form = ref({
  business_case_id: 0,
  budget_item_id: 0,
  owner_group_id: 0,
  title: '',
  description: '',
  spend_category: 'OPEX',
  requested_amount: 0,
  currency: 'USD',
  planned_commit_date: '',
  status: 'Draft'
})

const spendCategories = ['CAPEX', 'OPEX']
const statuses = ['Draft', 'Submitted', 'Approved', 'Rejected', 'Allocated']

const fetchBusinessCases = async () => {
  try {
    const res = await useApiFetch<BusinessCase[]>('/business-cases?limit=100')
    businessCases.value = res as any
  } catch (e: any) {
    console.error('Failed to load business cases:', e)
  }
}

const fetchBudgetItems = async () => {
  try {
    const res = await useApiFetch<BudgetItem[]>('/budget-items?limit=100')
    budgetItems.value = res as any
  } catch (e: any) {
    console.error('Failed to load budget items:', e)
  }
}

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
    let url = '/business-case-line-items?limit=100'
    if (filterBusinessCase.value) {
      url += `&business_case_id=${filterBusinessCase.value}`
    }
    if (filterSpendCategory.value) {
      url += `&spend_category=${filterSpendCategory.value}`
    }
    const res = await useApiFetch<LineItem[]>(url)
    items.value = res as any
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load line items.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    business_case_id: businessCases.value[0]?.id || 0,
    budget_item_id: budgetItems.value[0]?.id || 0,
    owner_group_id: groups.value[0]?.id || 0,
    title: '',
    description: '',
    spend_category: 'OPEX',
    requested_amount: 0,
    currency: 'USD',
    planned_commit_date: '',
    status: 'Draft'
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (item: LineItem) => {
  selectedItem.value = item
  form.value = {
    business_case_id: item.business_case_id,
    budget_item_id: item.budget_item_id,
    owner_group_id: item.owner_group_id,
    title: item.title,
    description: item.description || '',
    spend_category: item.spend_category,
    requested_amount: item.requested_amount,
    currency: item.currency,
    planned_commit_date: item.planned_commit_date || '',
    status: item.status || 'Draft'
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
    await useApiFetch('/business-case-line-items', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to create line item: ${e.data?.detail || e.message}`)
  }
}

const updateItem = async () => {
  if (!selectedItem.value) return
  try {
    await useApiFetch(`/business-case-line-items/${selectedItem.value.id}`, {
      method: 'PUT',
      body: {
        title: form.value.title,
        description: form.value.description,
        spend_category: form.value.spend_category,
        requested_amount: form.value.requested_amount,
        currency: form.value.currency,
        planned_commit_date: form.value.planned_commit_date,
        status: form.value.status
      }
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to update line item: ${e.data?.detail || e.message}`)
  }
}

const deleteItem = async (item: LineItem) => {
  if (!confirm(`Are you sure you want to delete line item "${item.title}"?`)) {
    return
  }
  try {
    await useApiFetch(`/business-case-line-items/${item.id}`, {
      method: 'DELETE'
    })
    await fetchItems()
  } catch (e: any) {
    console.error(e)
    alert(`Failed to delete line item: ${e.data?.detail || e.message}`)
  }
}

const canEdit = (item: LineItem) => {
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

const getBusinessCaseTitle = (id: number) => {
  return businessCases.value.find(bc => bc.id === id)?.title || 'Unknown'
}

const getBudgetItemRef = (id: number) => {
  return budgetItems.value.find(bi => bi.id === id)?.workday_ref || 'Unknown'
}

const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

onMounted(async () => {
  await Promise.all([
    fetchBusinessCases(),
    fetchBudgetItems(),
    fetchGroups()
  ])
  await fetchItems()
})
</script>

<template>
  <section class="card">
    <div class="header-row">
      <div>
        <h1 class="card-title">Business Case Line Items</h1>
        <p class="card-sub">Link business cases to budget items and allocate funds</p>
      </div>
      <button @click="openCreateModal" class="btn-primary">
        + Create Line Item
      </button>
    </div>

    <!-- Filters -->
    <div class="filters">
      <div class="filter-group">
        <label>Business Case:</label>
        <select v-model="filterBusinessCase" @change="fetchItems">
          <option :value="null">All Business Cases</option>
          <option v-for="bc in businessCases" :key="bc.id" :value="bc.id">
            {{ bc.title }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label>Spend Category:</label>
        <select v-model="filterSpendCategory" @change="fetchItems">
          <option :value="null">All Categories</option>
          <option v-for="cat in spendCategories" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>
      </div>
    </div>

    <p v-if="loading">Loading…</p>
    <p v-else-if="error" style="color: #cc0000;">{{ error }}</p>
    <div v-else-if="items.length === 0" class="empty-state">
      No line items found. Click "Create Line Item" to add one.
    </div>
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>Title</th>
          <th>Business Case</th>
          <th>Budget Item</th>
          <th>Category</th>
          <th>Requested Amount</th>
          <th>Owner Group</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>
            <strong>{{ item.title }}</strong>
            <div v-if="item.description" class="description">{{ item.description }}</div>
          </td>
          <td class="text-small">{{ getBusinessCaseTitle(item.business_case_id) }}</td>
          <td><code class="code-ref">{{ getBudgetItemRef(item.budget_item_id) }}</code></td>
          <td>
            <span
              class="badge badge-category"
              :class="item.spend_category === 'CAPEX' ? 'badge-capex' : 'badge-opex'"
            >
              {{ item.spend_category }}
            </span>
          </td>
          <td class="amount">{{ formatCurrency(item.requested_amount, item.currency) }}</td>
          <td>
            <span class="badge badge-group">
              {{ getGroupName(item.owner_group_id) }}
            </span>
          </td>
          <td>{{ item.status || 'Draft' }}</td>
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
        <h2>Create Line Item</h2>
        <form @submit.prevent="createItem">
          <div class="form-group">
            <label>Business Case <span class="required">*</span></label>
            <select v-model.number="form.business_case_id" required>
              <option v-for="bc in businessCases" :key="bc.id" :value="bc.id">
                {{ bc.title }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Budget Item <span class="required">*</span></label>
            <select v-model.number="form.budget_item_id" required>
              <option v-for="bi in budgetItems" :key="bi.id" :value="bi.id">
                {{ bi.workday_ref }} - {{ bi.title }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Owner Group <span class="required">*</span></label>
            <select v-model.number="form.owner_group_id" required>
              <option v-for="group in groups" :key="group.id" :value="group.id">
                {{ group.name }}
              </option>
            </select>
            <small>This group will own all child records (WBS, Assets, POs, etc.)</small>
          </div>

          <div class="form-group">
            <label>Title <span class="required">*</span></label>
            <input
              v-model="form.title"
              type="text"
              placeholder="e.g., AWS EC2 Infrastructure"
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
              <label>Spend Category <span class="required">*</span></label>
              <select v-model="form.spend_category" required>
                <option v-for="cat in spendCategories" :key="cat" :value="cat">
                  {{ cat }}
                </option>
              </select>
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

          <div class="form-row">
            <div class="form-group">
              <label>Requested Amount <span class="required">*</span></label>
              <input
                v-model.number="form.requested_amount"
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
            <label>Planned Commit Date</label>
            <input
              v-model="form.planned_commit_date"
              type="date"
            />
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModals" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary">
              Create Line Item
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <h2>Edit Line Item</h2>
        <form @submit.prevent="updateItem">
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
              <label>Spend Category <span class="required">*</span></label>
              <select v-model="form.spend_category" required>
                <option v-for="cat in spendCategories" :key="cat" :value="cat">
                  {{ cat }}
                </option>
              </select>
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

          <div class="form-row">
            <div class="form-group">
              <label>Requested Amount <span class="required">*</span></label>
              <input
                v-model.number="form.requested_amount"
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
            <label>Planned Commit Date</label>
            <input
              v-model="form.planned_commit_date"
              type="date"
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
  min-width: 200px;
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

.text-small {
  font-size: 0.85rem;
}

.code-ref {
  background-color: var(--color-background-soft);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-family: 'Courier New', monospace;
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

.badge-category {
  color: white;
}

.badge-capex {
  background-color: #8b5cf6;
}

.badge-opex {
  background-color: #3b82f6;
}

.badge-group {
  background-color: var(--color-primary);
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
