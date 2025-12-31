<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

interface Resource {
  id: number
  name: string
  vendor?: string
  role?: string
  start_date?: string
  end_date?: string
  cost_per_month?: string  // Changed from number for Decimal precision
  owner_group_id: number
  status?: string
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface Group {
  id: number
  name: string
}

const userCookie = useCookie('user_info')
const user = computed(() => userCookie.value)

const items = ref<Resource[]>([])
const groups = ref<Group[]>([])

const showCreateModal = ref(false)
const showEditModal = ref(false)

const form = ref({
  name: '',
  vendor: '',
  role: '',
  start_date: '',
  end_date: '',
  cost_per_month: '',
  owner_group_id: 0,
  status: 'Active'
})

const editingItem = ref<Resource | null>(null)

// Filters
const filterStatus = ref('')
const filterVendor = ref('')
const filterOwnerGroup = ref(0)

const statuses = ['Active', 'Inactive', 'On Leave', 'Terminated']

// Fetch data
const fetchItems = async () => {
  try {
    const data = await useApiFetch('/resources', { method: 'GET' })
    items.value = data as Resource[]
  } catch (e: any) {
    alert(`Failed to fetch resources: ${e.data?.detail || e.message}`)
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
  fetchGroups()
})

// Computed
const filteredItems = computed(() => {
  let result = items.value
  if (filterStatus.value) {
    result = result.filter(item => item.status === filterStatus.value)
  }
  if (filterVendor.value) {
    result = result.filter(item =>
      item.vendor?.toLowerCase().includes(filterVendor.value.toLowerCase())
    )
  }
  if (filterOwnerGroup.value) {
    result = result.filter(item => item.owner_group_id === filterOwnerGroup.value)
  }
  return result
})

// Helpers
const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

const getStatusColor = (status?: string) => {
  const colors: Record<string, string> = {
    'Active': '#10b981',
    'Inactive': '#6b7280',
    'On Leave': '#f59e0b',
    'Terminated': '#ef4444'
  }
  return colors[status || 'Active'] || '#6b7280'
}

const formatCurrency = (amount?: string | number) => {
  if (!amount) return '-'
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

// Permissions
const canEdit = (item: Resource) => {
  if (!user.value) return false
  if (user.value.role === 'Admin') return true
  if (user.value.role === 'Manager') return true
  return item.created_by === user.value.id
}

const canDelete = (item: Resource) => {
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
    name: '',
    vendor: '',
    role: '',
    start_date: '',
    end_date: '',
    cost_per_month: '',
    owner_group_id: 0,
    status: 'Active'
  }
  showCreateModal.value = true
}

const openEditModal = (item: Resource) => {
  editingItem.value = item
  form.value = {
    name: item.name,
    vendor: item.vendor || '',
    role: item.role || '',
    start_date: item.start_date || '',
    end_date: item.end_date || '',
    cost_per_month: item.cost_per_month || 0,
    owner_group_id: item.owner_group_id,
    status: item.status || 'Active'
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
    if (!form.value.name.trim()) {
      alert('Name is required')
      return
    }
    if (!form.value.owner_group_id) {
      alert('Please select an owner group')
      return
    }

    await useApiFetch('/resources', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    alert(`Failed to create resource: ${e.data?.detail || e.message}`)
  }
}

const updateItem = async () => {
  if (!editingItem.value) return
  try {
    await useApiFetch(`/resources/${editingItem.value.id}`, {
      method: 'PUT',
      body: {
        name: form.value.name,
        vendor: form.value.vendor,
        role: form.value.role,
        start_date: form.value.start_date,
        end_date: form.value.end_date,
        cost_per_month: form.value.cost_per_month,
        status: form.value.status
      }
    })
    await fetchItems()
    closeModals()
  } catch (e: any) {
    alert(`Failed to update resource: ${e.data?.detail || e.message}`)
  }
}

const deleteItem = async (item: Resource) => {
  if (!confirm(`Are you sure you want to delete resource "${item.name}"?`)) return
  try {
    await useApiFetch(`/resources/${item.id}`, { method: 'DELETE' })
    await fetchItems()
  } catch (e: any) {
    alert(`Failed to delete resource: ${e.data?.detail || e.message}`)
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>Resources</h1>
      <button v-if="canCreate" @click="openCreateModal" class="btn-primary">+ Create Resource</button>
    </div>

    <!-- Filters -->
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 200px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Status</label>
        <select v-model="filterStatus" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
          <option value="">All Statuses</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div style="flex: 1; min-width: 200px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Vendor</label>
        <input v-model="filterVendor" type="text" placeholder="Search vendor..." style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" />
      </div>
      <div style="flex: 1; min-width: 200px;">
        <label style="display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #666;">Owner Group</label>
        <select v-model.number="filterOwnerGroup" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
          <option :value="0">All Groups</option>
          <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
        </select>
      </div>
    </div>

    <!-- List -->
    <div v-if="filteredItems.length === 0" class="empty-state">
      <p>No resources found</p>
      <button v-if="canCreate" @click="openCreateModal" class="btn-primary">Create First Resource</button>
    </div>

    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Vendor</th>
            <th>Role</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Cost/Month</th>
            <th>Owner Group</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredItems" :key="item.id">
            <td><strong>{{ item.name }}</strong></td>
            <td>{{ item.vendor || '-' }}</td>
            <td>{{ item.role || '-' }}</td>
            <td>{{ formatDate(item.start_date) }}</td>
            <td>{{ formatDate(item.end_date) }}</td>
            <td>{{ formatCurrency(item.cost_per_month) }}</td>
            <td>{{ getGroupName(item.owner_group_id) }}</td>
            <td>
              <span class="badge" :style="{ backgroundColor: getStatusColor(item.status) }">
                {{ item.status || 'Active' }}
              </span>
            </td>
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
          <h2>Create Resource</h2>
          <button @click="closeModals" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="form.name" type="text" placeholder="Resource name" required />
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Vendor</label>
              <input v-model="form.vendor" type="text" placeholder="Vendor/company name" />
            </div>
            <div class="form-group">
              <label>Role</label>
              <input v-model="form.role" type="text" placeholder="e.g., Developer, Consultant" />
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
              <label>Cost per Month (USD)</label>
              <input v-model="form.cost_per_month" type="text" step="0.01" min="0" />
            </div>
            <div class="form-group">
              <label>Status</label>
              <select v-model="form.status">
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Owner Group *</label>
            <select v-model.number="form.owner_group_id" required>
              <option :value="0" disabled>Select an owner group</option>
              <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
            </select>
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
          <h2>Edit Resource</h2>
          <button @click="closeModals" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="form.name" type="text" required />
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label>Vendor</label>
              <input v-model="form.vendor" type="text" />
            </div>
            <div class="form-group">
              <label>Role</label>
              <input v-model="form.role" type="text" />
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
              <label>Cost per Month (USD)</label>
              <input v-model="form.cost_per_month" type="text" step="0.01" min="0" />
            </div>
            <div class="form-group">
              <label>Status</label>
              <select v-model="form.status">
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Owner Group</label>
            <input :value="getGroupName(form.owner_group_id)" type="text" disabled />
            <p style="font-size: 0.85rem; color: #666; margin: 0.25rem 0 0 0;">Cannot change owner group after creation</p>
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
