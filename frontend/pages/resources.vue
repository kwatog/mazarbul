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

interface Resource {
  id: number
  name: string
  vendor?: string
  role?: string
  start_date?: string
  end_date?: string
  cost_per_month?: string
  owner_group_id: number
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

const items = ref<Resource[]>([])
const groups = ref<UserGroup[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const filterStatus = ref<string | null>(null)
const filterVendor = ref('')
const filterOwnerGroup = ref<number | null>(null)

const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedItem = ref<Resource | null>(null)

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

const statuses = ['Active', 'Inactive', 'On Leave', 'Terminated']

const statusOptions = computed(() =>
  statuses.map(s => ({ value: s, label: s }))
)

const groupOptions = computed(() =>
  groups.value.map(g => ({ value: g.id, label: g.name }))
)

const fetchGroups = async () => {
  try {
    const res = await useApiFetch<UserGroup[]>('/user-groups')
    groups.value = res as any
    if (groups.value.length > 0 && form.value.owner_group_id === 0) {
      form.value.owner_group_id = groups.value[0].id
    }
  } catch (e: any) {
    console.error('Failed to load groups:', e)
  }
}

const fetchItems = async () => {
  try {
    loading.value = true
    const data = await useApiFetch('/resources', { method: 'GET' })
    items.value = data as Resource[]
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load resources.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

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

const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

const getStatusVariant = (status?: string): 'success' | 'warning' | 'danger' | 'secondary' => {
  const variants: Record<string, 'success' | 'warning' | 'danger' | 'secondary'> = {
    'Active': 'success',
    'Inactive': 'secondary',
    'On Leave': 'warning',
    'Terminated': 'danger'
  }
  return variants[status || 'Active'] || 'secondary'
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

const canEdit = (item: Resource) => {
  if (!currentUser) return false
  if (['Admin', 'Manager'].includes(currentUser.role)) return true
  return item.created_by === currentUser.id
}

const canDelete = () => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
}

const canCreate = computed(() => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
})

const resetForm = () => {
  form.value = {
    name: '',
    vendor: '',
    role: '',
    start_date: '',
    end_date: '',
    cost_per_month: '',
    owner_group_id: groups.value[0]?.id || 0,
    status: 'Active'
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (item: Resource) => {
  selectedItem.value = item
  form.value = {
    name: item.name,
    vendor: item.vendor || '',
    role: item.role || '',
    start_date: item.start_date || '',
    end_date: item.end_date || '',
    cost_per_month: item.cost_per_month || '',
    owner_group_id: item.owner_group_id,
    status: item.status || 'Active'
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
    if (!form.value.name.trim()) {
      showError('Name is required')
      return
    }
    if (!form.value.owner_group_id) {
      showError('Please select an owner group')
      return
    }

    loading.value = true
    await useApiFetch('/resources', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
    success('Resource created successfully!')
  } catch (e: any) {
    showError(`Failed to create resource: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const updateItem = async () => {
  if (!selectedItem.value) return
  try {
    loading.value = true
    await useApiFetch(`/resources/${selectedItem.value.id}`, {
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
    success('Resource updated successfully!')
  } catch (e: any) {
    showError(`Failed to update resource: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const deleteItem = async (item: Resource) => {
  if (!confirm(`Are you sure you want to delete resource "${item.name}"?`)) {
    return
  }
  try {
    loading.value = true
    await useApiFetch(`/resources/${item.id}`, { method: 'DELETE' })
    await fetchItems()
    success('Resource deleted successfully!')
  } catch (e: any) {
    showError(`Failed to delete resource: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const tableColumns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'vendor', label: 'Vendor', sortable: true },
  { key: 'role', label: 'Role', sortable: true },
  { key: 'start_date', label: 'Start Date', sortable: true, align: 'center' as const },
  { key: 'end_date', label: 'End Date', sortable: true, align: 'center' as const },
  { key: 'cost_per_month', label: 'Cost/Month', sortable: true, align: 'right' as const },
  { key: 'owner_group', label: 'Owner Group', sortable: false },
  { key: 'status', label: 'Status', sortable: true, align: 'center' as const },
  { key: 'actions', label: 'Actions', sortable: false }
]

onMounted(async () => {
  await fetchGroups()
  await fetchItems()
})
</script>

<template>
  <BaseCard title="Resources" subtitle="Manage team members and contractors">
    <template #header>
      <div class="header-actions">
        <BaseButton v-if="canCreate" variant="primary" @click="openCreateModal">
          + Create Resource
        </BaseButton>
      </div>
    </template>

    <div class="filters">
      <BaseSelect
        v-model="filterStatus"
        :options="[{ value: null, label: 'All Statuses' }, ...statusOptions]"
        label="Status"
      />
      <BaseInput
        v-model="filterVendor"
        label="Vendor"
        placeholder="Search vendor..."
      />
      <BaseSelect
        v-model="filterOwnerGroup"
        :options="[{ value: null, label: 'All Groups' }, ...groupOptions]"
        label="Owner Group"
      />
    </div>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" label="Loading resources..." />
    </div>

    <p v-else-if="error" class="error-message" role="alert">{{ error }}</p>

    <EmptyState
      v-else-if="filteredItems.length === 0"
      title="No resources found"
      description="Click 'Create Resource' to add your first team member or contractor."
      :action-text="canCreate ? 'Create Resource' : undefined"
      @action="openCreateModal"
    />

    <BaseTable
      v-else
      :columns="tableColumns"
      :data="filteredItems"
      :loading="loading"
      selectable
      sticky-header
      empty-message="No resources found"
      @row-click="openEditModal"
    >
      <template #cell-name="{ value }">
        <strong>{{ value }}</strong>
      </template>

      <template #cell-vendor="{ value }">
        {{ value || '-' }}
      </template>

      <template #cell-role="{ value }">
        {{ value || '-' }}
      </template>

      <template #cell-start_date="{ value }">
        {{ formatDate(value) }}
      </template>

      <template #cell-end_date="{ value }">
        {{ formatDate(value) }}
      </template>

      <template #cell-cost_per_month="{ value }">
        {{ formatCurrency(value) }}
      </template>

      <template #cell-owner_group="{ row }">
        <BaseBadge variant="primary" size="sm">{{ getGroupName(row.owner_group_id) }}</BaseBadge>
      </template>

      <template #cell-status="{ value }">
        <BaseBadge :variant="getStatusVariant(value)" size="sm">{{ value || 'Active' }}</BaseBadge>
      </template>

      <template #cell-actions="{ row }">
        <div class="action-buttons" v-if="canEdit(row) || canDelete()">
          <BaseButton
            v-if="canEdit(row)"
            size="sm"
            variant="secondary"
            @click.stop="openEditModal(row)"
          >
            Edit
          </BaseButton>
          <BaseButton
            v-if="canDelete()"
            size="sm"
            variant="danger"
            @click.stop="deleteItem(row)"
          >
            Delete
          </BaseButton>
        </div>
      </template>
    </BaseTable>

    <BaseModal v-model="showCreateModal" title="Create Resource" size="lg">
      <form @submit.prevent="createItem">
        <BaseInput
          v-model="form.name"
          label="Name"
          placeholder="e.g., John Doe"
          required
        />

        <div class="form-row">
          <BaseInput
            v-model="form.vendor"
            label="Vendor"
            placeholder="Vendor/company name"
          />
          <BaseInput
            v-model="form.role"
            label="Role"
            placeholder="e.g., Developer, Consultant"
          />
        </div>

        <div class="form-row">
          <BaseInput
            v-model="form.start_date"
            label="Start Date"
            type="date"
          />
          <BaseInput
            v-model="form.end_date"
            label="End Date"
            type="date"
          />
        </div>

        <div class="form-row">
          <BaseInput
            v-model="form.cost_per_month"
            label="Cost per Month (USD)"
            placeholder="0.00"
            type="text"
          />
          <BaseSelect
            v-model="form.status"
            :options="statusOptions"
            label="Status"
            required
          />
        </div>

        <BaseSelect
          v-model="form.owner_group_id"
          :options="groupOptions"
          label="Owner Group"
          required
        />
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="createItem">
          Create Resource
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal v-model="showEditModal" title="Edit Resource" size="lg">
      <form @submit.prevent="updateItem">
        <BaseInput
          v-model="form.name"
          label="Name"
          required
        />

        <div class="form-row">
          <BaseInput
            v-model="form.vendor"
            label="Vendor"
          />
          <BaseInput
            v-model="form.role"
            label="Role"
          />
        </div>

        <div class="form-row">
          <BaseInput
            v-model="form.start_date"
            label="Start Date"
            type="date"
          />
          <BaseInput
            v-model="form.end_date"
            label="End Date"
            type="date"
          />
        </div>

        <div class="form-row">
          <BaseInput
            v-model="form.cost_per_month"
            label="Cost per Month (USD)"
            type="text"
          />
          <BaseSelect
            v-model="form.status"
            :options="statusOptions"
            label="Status"
            required
          />
        </div>

        <BaseInput
          :model-value="getGroupName(form.owner_group_id)"
          label="Owner Group"
          disabled
          help-text="Owner group cannot be changed after creation"
        />
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="updateItem">
          Save Changes
        </BaseButton>
      </template>
    </BaseModal>
  </BaseCard>
</template>

<style scoped>
.header-actions {
  display: flex;
  justify-content: flex-end;
}

.filters {
  display: flex;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
  padding: var(--spacing-4);
  background: var(--color-gray-50);
  border-radius: var(--radius-lg);
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: var(--spacing-12);
}

.error-message {
  color: var(--color-error);
  padding: var(--spacing-4);
  text-align: center;
}

.action-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
}

@media (max-width: 640px) {
  .filters {
    flex-direction: column;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
