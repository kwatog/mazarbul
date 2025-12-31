<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

interface PurchaseOrder {
  id: number
  asset_id: number
  po_number: string
  ariba_pr_number?: string
  supplier?: string
  po_type?: string
  start_date?: string
  end_date?: string
  total_amount: string  // Changed from number for Decimal precision
  currency: string
  spend_category: string
  planned_commit_date?: string
  actual_commit_date?: string
  owner_group_id: number
  status?: string
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface Asset {
  id: number
  asset_code: string
  wbs_id: number
}

interface Group {
  id: number
  name: string
}

const userCookie = useCookie('user_info')
const user = computed(() => userCookie.value)

const items = ref<PurchaseOrder[]>([])
const assets = ref<Asset[]>([])
const groups = ref<Group[]>([])

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showAccessModal = ref(false)

const form = ref({
  asset_id: 0,
  po_number: '',
  ariba_pr_number: '',
  supplier: '',
  po_type: '',
  start_date: '',
  end_date: '',
  total_amount: '',
  currency: 'USD',
  spend_category: 'CAPEX',
  planned_commit_date: '',
  actual_commit_date: '',
  owner_group_id: 0,
  status: 'Open'
})

const editingItem = ref<PurchaseOrder | null>(null)
const selectedPO = ref<PurchaseOrder | null>(null)

// Filters
const filterStatus = ref('')
const filterAsset = ref(0)
const filterSpendCategory = ref('')
const filterSupplier = ref('')

const statuses = ['Open', 'Approved', 'In Progress', 'Completed', 'Cancelled']
const spendCategories = ['CAPEX', 'OPEX']
const poTypes = ['Standard', 'Contract', 'Blanket', 'Services']

// Fetch data
const fetchItems = async () => {
  try {
    const data = await useApiFetch('/purchase-orders', { method: 'GET' })
    items.value = data as PurchaseOrder[]
  } catch (e: any) {
    alert(`Failed to fetch purchase orders: ${e.data?.detail || e.message}`)
  }
}

const fetchAssets = async () => {
  try {
    const data = await useApiFetch('/assets', { method: 'GET' })
    assets.value = data as Asset[]
  } catch (e: any) {
    console.error('Failed to fetch assets:', e)
  }
}

const fetchGroups = async () => {
  try {
    const data = await useApiFetch('/groups', { method: 'GET' })
    groups.value = data as Group[]
  } catch (e: any) {
    console.error('Failed to fetch groups:', e)
  }
}

onMounted(() => {
  fetchItems()
  fetchAssets()
  fetchGroups()
})

// Computed
const filteredItems = computed(() => {
  let result = items.value
  if (filterStatus.value) {
    result = result.filter(item => item.status === filterStatus.value)
  }
  if (filterAsset.value) {
    result = result.filter(item => item.asset_id === filterAsset.value)
  }
  if (filterSpendCategory.value) {
    result = result.filter(item => item.spend_category === filterSpendCategory.value)
  }
  if (filterSupplier.value) {
    result = result.filter(item =>
      item.supplier?.toLowerCase().includes(filterSupplier.value.toLowerCase())
    )
  }
  return result
})

// Helpers
const getAssetCode = (id: number) => {
  return assets.value.find(a => a.id === id)?.asset_code || 'Unknown'
}

const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

const getStatusColor = (status?: string) => {
  const colors: Record<string, string> = {
    'Open': '#3b82f6',
    'Approved': '#10b981',
    'In Progress': '#f59e0b',
    'Completed': '#8b5cf6',
    'Cancelled': '#ef4444'
  }
  return colors[status || 'Open'] || '#6b7280'
}

const getSpendCategoryColor = (category?: string) => {
  return category === 'CAPEX' ? '#8b5cf6' : '#3b82f6'
}

const formatCurrency = (amount: string | number, currency: string) => {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD'
  }).format(num)
}

// Permissions
const canEdit = (item: PurchaseOrder) => {
  if (!user.value) return false
  if (user.value.role === 'Admin') return true
  if (user.value.role === 'Manager') return true
  return item.created_by === user.value.id
}

const canDelete = (item: PurchaseOrder) => {
  if (!user.value) return false
  if (user.value.role === 'Admin') return true
  if (user.value.role === 'Manager') return true
  return false
}

const canShareAccess = (item: PurchaseOrder) => {
  if (!user.value) return false
  if (['Admin', 'Manager'].includes(user.value.role)) return true
  return item.created_by === user.value.id
}

// CRUD operations
const openCreateModal = () => {
  form.value = {
    asset_id: 0,
    po_number: '',
    ariba_pr_number: '',
    supplier: '',
    po_type: '',
    start_date: '',
    end_date: '',
    total_amount: '',
    currency: 'USD',
    spend_category: 'CAPEX',
    planned_commit_date: '',
    actual_commit_date: '',
    owner_group_id: 0,
    status: 'Open'
  }
  showCreateModal.value = true
}

const openEditModal = (item: PurchaseOrder) => {
  editingItem.value = item
  form.value = {
    asset_id: item.asset_id,
    po_number: item.po_number,
    ariba_pr_number: item.ariba_pr_number || '',
    supplier: item.supplier || '',
    po_type: item.po_type || '',
    start_date: item.start_date || '',
    end_date: item.end_date || '',
    total_amount: item.total_amount,
    currency: item.currency,
    spend_category: item.spend_category,
    planned_commit_date: item.planned_commit_date || '',
    actual_commit_date: item.actual_commit_date || '',
    owner_group_id: item.owner_group_id,
    status: item.status || 'Open'
  }
  showEditModal.value = true
}

const openAccessModal = (item: PurchaseOrder) => {
  selectedPO.value = item
  showAccessModal.value = true
}

const closeModals = () => {
  showCreateModal.value = false
  showEditModal.value = false
  showAccessModal.value = false
  editingItem.value = null
  selectedPO.value = null
}

const createItem = async () => {
  try {
    if (!form.value.asset_id) {
      alert('Please select an asset')
      return
    }
    if (!form.value.po_number.trim()) {
      alert('PO Number is required')
      return
    }
    if (!form.value.total_amount || form.value.total_amount <= 0) {
      alert('Total Amount must be greater than 0')
      return
    }

    await useApiFetch('/purchase-orders', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    alert(`Failed to create purchase order: ${e.data?.detail || e.message}`)
  }
}

const updateItem = async () => {
  if (!editingItem.value) return
  try {
    await useApiFetch(`/purchase-orders/${editingItem.value.id}`, {
      method: 'PUT',
      body: {
        ariba_pr_number: form.value.ariba_pr_number,
        supplier: form.value.supplier,
        po_type: form.value.po_type,
        start_date: form.value.start_date,
        end_date: form.value.end_date,
        total_amount: form.value.total_amount,
        currency: form.value.currency,
        spend_category: form.value.spend_category,
        planned_commit_date: form.value.planned_commit_date,
        actual_commit_date: form.value.actual_commit_date,
        status: form.value.status
      }
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    alert(`Failed to update purchase order: ${e.data?.detail || e.message}`)
  }
}

const deleteItem = async (item: PurchaseOrder) => {
  if (!confirm(`Are you sure you want to delete PO "${item.po_number}"?`)) return
  try {
    await useApiFetch(`/purchase-orders/${item.id}`, { method: 'DELETE' })
    await fetchItems()
  } catch (e: any) {
    alert(`Failed to delete purchase order: ${e.data?.detail || e.message}`)
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>Purchase Orders</h1>
      <button @click="openCreateModal" class="btn-primary">+ Create PO</button>
    </div>

    <!-- Filters -->
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 180px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Status</label>
        <select v-model="filterStatus" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
          <option value="">All Statuses</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div style="flex: 1; min-width: 180px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Asset</label>
        <select v-model.number="filterAsset" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
          <option :value="0">All Assets</option>
          <option v-for="a in assets" :key="a.id" :value="a.id">{{ a.asset_code }}</option>
        </select>
      </div>
      <div style="flex: 1; min-width: 180px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Spend Category</label>
        <select v-model="filterSpendCategory" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
          <option value="">All Categories</option>
          <option v-for="sc in spendCategories" :key="sc" :value="sc">{{ sc }}</option>
        </select>
      </div>
      <div style="flex: 1; min-width: 180px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Supplier</label>
        <input v-model="filterSupplier" type="text" placeholder="Search supplier..." style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" />
      </div>
    </div>

    <!-- List -->
    <div v-if="filteredItems.length === 0" class="empty-state">
      <p>No purchase orders found</p>
      <button @click="openCreateModal" class="btn-primary">Create First PO</button>
    </div>

    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>PO Number</th>
            <th>Asset</th>
            <th>Supplier</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Status</th>
            <th>Owner Group</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredItems" :key="item.id">
            <td><strong>{{ item.po_number }}</strong></td>
            <td>{{ getAssetCode(item.asset_id) }}</td>
            <td>{{ item.supplier || '-' }}</td>
            <td>{{ formatCurrency(item.total_amount, item.currency) }}</td>
            <td>
              <span class="badge" :style="{ backgroundColor: getSpendCategoryColor(item.spend_category) }">
                {{ item.spend_category }}
              </span>
            </td>
            <td>
              <span class="badge" :style="{ backgroundColor: getStatusColor(item.status) }">
                {{ item.status || 'Open' }}
              </span>
            </td>
            <td>{{ getGroupName(item.owner_group_id) }}</td>
            <td>
              <div style="display: flex; gap: 0.5rem;">
                <button v-if="canEdit(item)" @click="openEditModal(item)" class="btn-sm">Edit</button>
                <button v-if="canDelete(item)" @click="deleteItem(item)" class="btn-sm btn-danger">Delete</button>
                <button v-if="canShareAccess(item)" @click="openAccessModal(item)" class="btn-sm" style="background-color: #10b981;">Share</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-content" style="max-width: 700px;">
        <div class="modal-header">
          <h2>Create Purchase Order</h2>
          <button @click="closeModals" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Asset *</label>
              <select v-model.number="form.asset_id" required>
                <option :value="0" disabled>Select an asset</option>
                <option v-for="a in assets" :key="a.id" :value="a.id">{{ a.asset_code }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>PO Number *</label>
              <input v-model="form.po_number" type="text" placeholder="e.g., PO-2025-001" required />
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Ariba PR Number</label>
              <input v-model="form.ariba_pr_number" type="text" placeholder="Optional" />
            </div>
            <div class="form-group">
              <label>Supplier</label>
              <input v-model="form.supplier" type="text" placeholder="Supplier name" />
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>PO Type</label>
              <select v-model="form.po_type">
                <option value="">Select type</option>
                <option v-for="pt in poTypes" :key="pt" :value="pt">{{ pt }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Spend Category *</label>
              <select v-model="form.spend_category" required>
                <option v-for="sc in spendCategories" :key="sc" :value="sc">{{ sc }}</option>
              </select>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Total Amount *</label>
              <input v-model="form.total_amount" type="text" step="0.01" min="0" required />
            </div>
            <div class="form-group">
              <label>Currency *</label>
              <select v-model="form.currency" required>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
            <div class="form-group">
              <label>Status</label>
              <select v-model="form.status">
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Start Date</label>
              <input v-model="form.start_date" type="date" />
            </div>
            <div class="form-group">
              <label>End Date</label>
              <input v-model="form.end_date" type="date" />
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Planned Commit Date</label>
              <input v-model="form.planned_commit_date" type="date" />
            </div>
            <div class="form-group">
              <label>Actual Commit Date</label>
              <input v-model="form.actual_commit_date" type="date" />
            </div>
          </div>

          <div class="form-group">
            <p style="font-size: 0.85rem; color: #666; margin: 0;">
              <strong>Note:</strong> Owner Group will be automatically inherited from the selected Asset.
            </p>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeModals" class="btn-secondary">Cancel</button>
          <button @click="createItem" class="btn-primary">Create</button>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-content" style="max-width: 700px;">
        <div class="modal-header">
          <h2>Edit Purchase Order</h2>
          <button @click="closeModals" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Asset</label>
              <input :value="getAssetCode(form.asset_id)" type="text" disabled />
              <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Cannot change parent entity</p>
            </div>
            <div class="form-group">
              <label>PO Number</label>
              <input :value="form.po_number" type="text" disabled />
              <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Cannot change PO number</p>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Ariba PR Number</label>
              <input v-model="form.ariba_pr_number" type="text" />
            </div>
            <div class="form-group">
              <label>Supplier</label>
              <input v-model="form.supplier" type="text" />
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>PO Type</label>
              <select v-model="form.po_type">
                <option value="">Select type</option>
                <option v-for="pt in poTypes" :key="pt" :value="pt">{{ pt }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Spend Category *</label>
              <select v-model="form.spend_category" required>
                <option v-for="sc in spendCategories" :key="sc" :value="sc">{{ sc }}</option>
              </select>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Total Amount *</label>
              <input v-model="form.total_amount" type="text" step="0.01" min="0" required />
            </div>
            <div class="form-group">
              <label>Currency *</label>
              <select v-model="form.currency" required>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
            <div class="form-group">
              <label>Status</label>
              <select v-model="form.status">
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Start Date</label>
              <input v-model="form.start_date" type="date" />
            </div>
            <div class="form-group">
              <label>End Date</label>
              <input v-model="form.end_date" type="date" />
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Planned Commit Date</label>
              <input v-model="form.planned_commit_date" type="date" />
            </div>
            <div class="form-group">
              <label>Actual Commit Date</label>
              <input v-model="form.actual_commit_date" type="date" />
            </div>
          </div>

          <div class="form-group">
            <label>Owner Group (Inherited)</label>
            <input :value="getGroupName(form.owner_group_id)" type="text" disabled />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Inherited from parent Asset</p>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeModals" class="btn-secondary">Cancel</button>
          <button @click="updateItem" class="btn-primary">Update</button>
        </div>
      </div>
    </div>

    <!-- Record Access Modal -->
    <RecordAccessModal
      v-if="selectedPO"
      :record-type="'PurchaseOrder'"
      :record-id="selectedPO.id"
      :is-open="showAccessModal"
      @close="closeModals"
      @updated="fetchItems"
    />
  </div>
</template>
