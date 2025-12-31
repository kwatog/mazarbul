<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

interface ResourceAllocation {
  id: number
  resource_id: number
  po_id: number
  allocation_start?: string
  allocation_end?: string
  expected_monthly_burn?: string  // Changed from number for Decimal precision
  owner_group_id: number
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface Resource {
  id: number
  name: string
  vendor?: string
  role?: string
}

interface PurchaseOrder {
  id: number
  po_number: string
  supplier?: string
  currency: string
}

interface Group {
  id: number
  name: string
}

const userCookie = useCookie('user_info')
const user = computed(() => userCookie.value)

const items = ref<ResourceAllocation[]>([])
const resources = ref<Resource[]>([])
const purchaseOrders = ref<PurchaseOrder[]>([])
const groups = ref<Group[]>([])

const showCreateModal = ref(false)
const showEditModal = ref(false)

const form = ref({
  resource_id: 0,
  po_id: 0,
  allocation_start: '',
  allocation_end: '',
  expected_monthly_burn: '',
  owner_group_id: 0
})

const editingItem = ref<ResourceAllocation | null>(null)

// Filters
const filterResource = ref(0)
const filterPO = ref(0)

// Fetch data
const fetchItems = async () => {
  try {
    const data = await useApiFetch('/allocations', { method: 'GET' })
    items.value = data as ResourceAllocation[]
  } catch (e: any) {
    alert(`Failed to fetch allocations: ${e.data?.detail || e.message}`)
  }
}

const fetchResources = async () => {
  try {
    const data = await useApiFetch('/resources', { method: 'GET' })
    resources.value = data as Resource[]
  } catch (e: any) {
    console.error('Failed to fetch resources:', e)
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
  fetchResources()
  fetchPurchaseOrders()
  fetchGroups()
})

// Computed
const filteredItems = computed(() => {
  let result = items.value
  if (filterResource.value) {
    result = result.filter(item => item.resource_id === filterResource.value)
  }
  if (filterPO.value) {
    result = result.filter(item => item.po_id === filterPO.value)
  }
  return result
})

// Helpers
const getResourceName = (id: number) => {
  const resource = resources.value.find(r => r.id === id)
  return resource ? `${resource.name}${resource.vendor ? ' (' + resource.vendor + ')' : ''}` : 'Unknown'
}

const getPONumber = (id: number) => {
  return purchaseOrders.value.find(po => po.id === id)?.po_number || 'Unknown'
}

const getPOCurrency = (id: number) => {
  return purchaseOrders.value.find(po => po.id === id)?.currency || 'USD'
}

const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

const formatCurrency = (amount?: string | number, poId?: number) => {
  if (!amount) return '-'
  const currency = poId ? getPOCurrency(poId) : 'USD'
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
const canEdit = (item: ResourceAllocation) => {
  if (!user.value) return false
  if (user.value.role === 'Admin') return true
  if (user.value.role === 'Manager') return true
  return item.created_by === user.value.id
}

const canDelete = (item: ResourceAllocation) => {
  if (!user.value) return false
  if (user.value.role === 'Admin') return true
  if (user.value.role === 'Manager') return true
  return false
}

const canCreate = computed(() => {
  if (!user.value) return false
  return ['Admin', 'Manager'].includes(user.value.role)
})

// CRUD operations
const openCreateModal = () => {
  form.value = {
    resource_id: 0,
    po_id: 0,
    allocation_start: '',
    allocation_end: '',
    expected_monthly_burn: '',
    owner_group_id: 0
  }
  showCreateModal.value = true
}

const openEditModal = (item: ResourceAllocation) => {
  editingItem.value = item
  form.value = {
    resource_id: item.resource_id,
    po_id: item.po_id,
    allocation_start: item.allocation_start || '',
    allocation_end: item.allocation_end || '',
    expected_monthly_burn: item.expected_monthly_burn || 0,
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
    if (!form.value.resource_id) {
      alert('Please select a resource')
      return
    }
    if (!form.value.po_id) {
      alert('Please select a purchase order')
      return
    }

    await useApiFetch('/allocations', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    alert(`Failed to create allocation: ${e.data?.detail || e.message}`)
  }
}

const updateItem = async () => {
  if (!editingItem.value) return
  try {
    await useApiFetch(`/allocations/${editingItem.value.id}`, {
      method: 'PUT',
      body: {
        allocation_start: form.value.allocation_start,
        allocation_end: form.value.allocation_end,
        expected_monthly_burn: form.value.expected_monthly_burn
      }
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    alert(`Failed to update allocation: ${e.data?.detail || e.message}`)
  }
}

const deleteItem = async (item: ResourceAllocation) => {
  if (!confirm('Are you sure you want to delete this allocation?')) return
  try {
    await useApiFetch(`/allocations/${item.id}`, { method: 'DELETE' })
    await fetchItems()
  } catch (e: any) {
    alert(`Failed to delete allocation: ${e.data?.detail || e.message}`)
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>Resource Allocations</h1>
      <button v-if="canCreate" @click="openCreateModal" class="btn-primary">+ Create Allocation</button>
    </div>

    <!-- Filters -->
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 250px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Resource</label>
        <select v-model.number="filterResource" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
          <option :value="0">All Resources</option>
          <option v-for="r in resources" :key="r.id" :value="r.id">
            {{ r.name }}{{ r.vendor ? ' (' + r.vendor + ')' : '' }}
          </option>
        </select>
      </div>
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
      <p>No allocations found</p>
      <button v-if="canCreate" @click="openCreateModal" class="btn-primary">Create First Allocation</button>
    </div>

    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Resource</th>
            <th>Purchase Order</th>
            <th>Allocation Start</th>
            <th>Allocation End</th>
            <th>Monthly Burn</th>
            <th>Owner Group</th>
            <th>Created By</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredItems" :key="item.id">
            <td><strong>{{ getResourceName(item.resource_id) }}</strong></td>
            <td>{{ getPONumber(item.po_id) }}</td>
            <td>{{ formatDate(item.allocation_start) }}</td>
            <td>{{ formatDate(item.allocation_end) }}</td>
            <td>{{ formatCurrency(item.expected_monthly_burn, item.po_id) }}</td>
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
          <h2>Create Resource Allocation</h2>
          <button @click="closeModals" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Resource *</label>
            <select v-model.number="form.resource_id" required>
              <option :value="0" disabled>Select a resource</option>
              <option v-for="r in resources" :key="r.id" :value="r.id">
                {{ r.name }}{{ r.vendor ? ' (' + r.vendor + ')' : '' }}{{ r.role ? ' - ' + r.role : '' }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Purchase Order *</label>
            <select v-model.number="form.po_id" required>
              <option :value="0" disabled>Select a purchase order</option>
              <option v-for="po in purchaseOrders" :key="po.id" :value="po.id">
                {{ po.po_number }}{{ po.supplier ? ' - ' + po.supplier : '' }}
              </option>
            </select>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Allocation Start</label>
              <input v-model="form.allocation_start" type="date" />
            </div>
            <div class="form-group">
              <label>Allocation End</label>
              <input v-model="form.allocation_end" type="date" />
            </div>
          </div>
          <div class="form-group">
            <label>Expected Monthly Burn</label>
            <input v-model="form.expected_monthly_burn" type="text" step="0.01" min="0" />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Amount in PO currency</p>
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
          <h2>Edit Resource Allocation</h2>
          <button @click="closeModals" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Resource</label>
            <input :value="getResourceName(form.resource_id)" type="text" disabled />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Cannot change resource after creation</p>
          </div>
          <div class="form-group">
            <label>Purchase Order</label>
            <input :value="getPONumber(form.po_id)" type="text" disabled />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Cannot change purchase order after creation</p>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Allocation Start</label>
              <input v-model="form.allocation_start" type="date" />
            </div>
            <div class="form-group">
              <label>Allocation End</label>
              <input v-model="form.allocation_end" type="date" />
            </div>
          </div>
          <div class="form-group">
            <label>Expected Monthly Burn</label>
            <input v-model="form.expected_monthly_burn" type="text" step="0.01" min="0" />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Amount in PO currency</p>
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
