<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

interface GoodsReceipt {
  id: number
  po_id: number
  gr_number: string
  gr_date?: string
  amount: string  // Changed from number for Decimal precision
  description?: string
  owner_group_id: number
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface PurchaseOrder {
  id: number
  po_number: string
  supplier?: string
  total_amount: string  // Changed from number for Decimal precision
  currency: string
}

interface Group {
  id: number
  name: string
}

const userCookie = useCookie('user_info')
const user = computed(() => userCookie.value)

const items = ref<GoodsReceipt[]>([])
const purchaseOrders = ref<PurchaseOrder[]>([])
const groups = ref<Group[]>([])

const showCreateModal = ref(false)
const showEditModal = ref(false)

const form = ref({
  po_id: 0,
  gr_number: '',
  gr_date: '',
  amount: '',
  description: '',
  owner_group_id: 0
})

const editingItem = ref<GoodsReceipt | null>(null)

// Filters
const filterPO = ref(0)

// Fetch data
const fetchItems = async () => {
  try {
    const data = await useApiFetch('/goods-receipts', { method: 'GET' })
    items.value = data as GoodsReceipt[]
  } catch (e: any) {
    alert(`Failed to fetch goods receipts: ${e.data?.detail || e.message}`)
  }
}

const fetchPurchaseOrders = async () => {
  try {
    const data = await useApiFetch('/purchase-orders', { method: 'GET' })
    purchaseOrders.value = data as PurchaseOrder[]
  } catch (e: any) {
    console.error('Failed to fetch purchase orders:', e)
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
  fetchPurchaseOrders()
  fetchGroups()
})

// Computed
const filteredItems = computed(() => {
  let result = items.value
  if (filterPO.value) {
    result = result.filter(item => item.po_id === filterPO.value)
  }
  return result
})

// Helpers
const getPONumber = (id: number) => {
  return purchaseOrders.value.find(po => po.id === id)?.po_number || 'Unknown'
}

const getPOCurrency = (id: number) => {
  return purchaseOrders.value.find(po => po.id === id)?.currency || 'USD'
}

const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

const formatCurrency = (amount: string | number, poId: number) => {
  const currency = getPOCurrency(poId)
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(num)
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

// Permissions
const canEdit = (item: GoodsReceipt) => {
  if (!user.value) return false
  if (user.value.role === 'Admin') return true
  if (user.value.role === 'Manager') return true
  return item.created_by === user.value.id
}

const canDelete = (item: GoodsReceipt) => {
  if (!user.value) return false
  if (user.value.role === 'Admin') return true
  if (user.value.role === 'Manager') return true
  return false
}

// CRUD operations
const openCreateModal = () => {
  form.value = {
    po_id: 0,
    gr_number: '',
    gr_date: new Date().toISOString().split('T')[0],
    amount: '',
    description: '',
    owner_group_id: 0
  }
  showCreateModal.value = true
}

const openEditModal = (item: GoodsReceipt) => {
  editingItem.value = item
  form.value = {
    po_id: item.po_id,
    gr_number: item.gr_number,
    gr_date: item.gr_date || '',
    amount: item.amount,
    description: item.description || '',
    owner_group_id: item.owner_group_id
  }
  showEditModal.value = true
}

const closeModals = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingItem.value = null
}

const createItem = async () => {
  try {
    if (!form.value.po_id) {
      alert('Please select a purchase order')
      return
    }
    if (!form.value.gr_number.trim()) {
      alert('GR Number is required')
      return
    }
    if (!form.value.amount || form.value.amount <= 0) {
      alert('Amount must be greater than 0')
      return
    }

    await useApiFetch('/goods-receipts', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    alert(`Failed to create goods receipt: ${e.data?.detail || e.message}`)
  }
}

const updateItem = async () => {
  if (!editingItem.value) return
  try {
    await useApiFetch(`/goods-receipts/${editingItem.value.id}`, {
      method: 'PUT',
      body: {
        gr_date: form.value.gr_date,
        amount: form.value.amount,
        description: form.value.description
      }
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    alert(`Failed to update goods receipt: ${e.data?.detail || e.message}`)
  }
}

const deleteItem = async (item: GoodsReceipt) => {
  if (!confirm(`Are you sure you want to delete goods receipt "${item.gr_number}"?`)) return
  try {
    await useApiFetch(`/goods-receipts/${item.id}`, { method: 'DELETE' })
    await fetchItems()
  } catch (e: any) {
    alert(`Failed to delete goods receipt: ${e.data?.detail || e.message}`)
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>Goods Receipts</h1>
      <button @click="openCreateModal" class="btn-primary">+ Create GR</button>
    </div>

    <!-- Filters -->
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 250px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Purchase Order</label>
        <select v-model.number="filterPO" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
          <option :value="0">All Purchase Orders</option>
          <option v-for="po in purchaseOrders" :key="po.id" :value="po.id">
            {{ po.po_number }}{{ po.supplier ? ' - ' + po.supplier : '' }}
          </option>
        </select>
      </div>
    </div>

    <!-- List -->
    <div v-if="filteredItems.length === 0" class="empty-state">
      <p>No goods receipts found</p>
      <button @click="openCreateModal" class="btn-primary">Create First Goods Receipt</button>
    </div>

    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>GR Number</th>
            <th>Purchase Order</th>
            <th>GR Date</th>
            <th>Amount</th>
            <th>Description</th>
            <th>Owner Group</th>
            <th>Created By</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredItems" :key="item.id">
            <td><strong>{{ item.gr_number }}</strong></td>
            <td>{{ getPONumber(item.po_id) }}</td>
            <td>{{ formatDate(item.gr_date) }}</td>
            <td>{{ formatCurrency(item.amount, item.po_id) }}</td>
            <td>{{ item.description || '-' }}</td>
            <td>{{ getGroupName(item.owner_group_id) }}</td>
            <td>User #{{ item.created_by }}</td>
            <td>
              <div style="display: flex; gap: 0.5rem;">
                <button v-if="canEdit(item)" @click="openEditModal(item)" class="btn-sm">Edit</button>
                <button v-if="canDelete(item)" @click="deleteItem(item)" class="btn-sm btn-danger">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Create Goods Receipt</h2>
          <button @click="closeModals" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Purchase Order *</label>
            <select v-model.number="form.po_id" required>
              <option :value="0" disabled>Select a purchase order</option>
              <option v-for="po in purchaseOrders" :key="po.id" :value="po.id">
                {{ po.po_number }}{{ po.supplier ? ' - ' + po.supplier : '' }} ({{ po.currency }} {{ po.total_amount }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>GR Number *</label>
            <input v-model="form.gr_number" type="text" placeholder="e.g., GR-2025-001" required />
          </div>
          <div class="form-group">
            <label>GR Date</label>
            <input v-model="form.gr_date" type="date" />
          </div>
          <div class="form-group">
            <label>Amount *</label>
            <input v-model="form.amount" type="text" step="0.01" min="0" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="form.description" rows="3" placeholder="Optional description"></textarea>
          </div>
          <div class="form-group">
            <p style="font-size: 0.85rem; color: #666; margin: 0;">
              <strong>Note:</strong> Owner Group will be automatically inherited from the selected Purchase Order.
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
      <div class="modal-content">
        <div class="modal-header">
          <h2>Edit Goods Receipt</h2>
          <button @click="closeModals" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Purchase Order</label>
            <input :value="getPONumber(form.po_id)" type="text" disabled />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Cannot change parent entity</p>
          </div>
          <div class="form-group">
            <label>GR Number</label>
            <input :value="form.gr_number" type="text" disabled />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Cannot change GR number</p>
          </div>
          <div class="form-group">
            <label>GR Date</label>
            <input v-model="form.gr_date" type="date" />
          </div>
          <div class="form-group">
            <label>Amount *</label>
            <input v-model="form.amount" type="text" step="0.01" min="0" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="form.description" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>Owner Group (Inherited)</label>
            <input :value="getGroupName(form.owner_group_id)" type="text" disabled />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Inherited from parent Purchase Order</p>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeModals" class="btn-secondary">Cancel</button>
          <button @click="updateItem" class="btn-primary">Update</button>
        </div>
      </div>
    </div>
  </div>
</template>
