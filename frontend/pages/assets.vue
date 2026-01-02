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

interface Asset {
  id: number
  wbs_id: number
  asset_code: string
  asset_type?: string
  description?: string
  owner_group_id: number
  status?: string
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface WBS {
  id: number
  wbs_code: string
  description?: string
}

interface Group {
  id: number
  name: string
}

const items = ref<Asset[]>([])
const wbsItems = ref<WBS[]>([])
const groups = ref<Group[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedItem = ref<Asset | null>(null)

const form = ref({
  wbs_id: 0,
  asset_code: '',
  asset_type: 'CAPEX',
  description: '',
  owner_group_id: 0,
  status: 'Active'
})

const filterStatus = ref<string | null>(null)
const filterWBS = ref<number | null>(null)
const filterAssetType = ref<string | null>(null)

const statuses = ['Active', 'Inactive', 'Disposed', 'Under Maintenance']
const assetTypes = ['CAPEX', 'OPEX', 'Lease']

const statusOptions = computed(() =>
  statuses.map(s => ({ value: s, label: s }))
)

const assetTypeOptions = computed(() =>
  assetTypes.map(t => ({ value: t, label: t }))
)

const wbsOptions = computed(() =>
  wbsItems.value.map(w => ({
    value: w.id,
    label: w.description ? `${w.wbs_code} - ${w.description}` : w.wbs_code
  }))
)

const groupOptions = computed(() =>
  groups.value.map(g => ({ value: g.id, label: g.name }))
)

// Fetch data
const fetchItems = async () => {
  try {
    loading.value = true
    const data = await useApiFetch('/assets', { method: 'GET' })
    items.value = data as Asset[]
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load assets.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

const fetchWBS = async () => {
  try {
    const data = await useApiFetch('/wbs', { method: 'GET' })
    wbsItems.value = data as WBS[]
  } catch (e: any) {
    console.error('Failed to fetch WBS items:', e)
  }
}

const fetchGroups = async () => {
  try {
    const data = await useApiFetch('/groups', { method: 'GET' })
    groups.value = data as Group[]
    if (groups.value.length > 0 && form.value.owner_group_id === 0) {
      form.value.owner_group_id = groups.value[0].id
    }
  } catch (e: any) {
    console.error('Failed to fetch groups:', e)
  }
}

onMounted(async () => {
  await fetchWBS()
  await fetchGroups()
  await fetchItems()
})

// Computed
const filteredItems = computed(() => {
  let result = items.value
  if (filterStatus.value) {
    result = result.filter(item => item.status === filterStatus.value)
  }
  if (filterWBS.value) {
    result = result.filter(item => item.wbs_id === filterWBS.value)
  }
  if (filterAssetType.value) {
    result = result.filter(item => item.asset_type === filterAssetType.value)
  }
  return result
})

// Helpers
const getWBSCode = (id: number) => {
  return wbsItems.value.find(w => w.id === id)?.wbs_code || 'Unknown'
}

const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

const getStatusVariant = (status?: string): 'success' | 'warning' | 'danger' | 'secondary' => {
  const variants: Record<string, 'success' | 'warning' | 'danger' | 'secondary'> = {
    'Active': 'success',
    'Inactive': 'secondary',
    'Disposed': 'danger',
    'Under Maintenance': 'warning'
  }
  return variants[status || 'Active'] || 'secondary'
}

const getAssetTypeVariant = (type?: string): 'primary' | 'info' | 'success' => {
  const variants: Record<string, 'primary' | 'info' | 'success'> = {
    'CAPEX': 'primary',
    'OPEX': 'info',
    'Lease': 'success'
  }
  return variants[type || 'CAPEX'] || 'primary'
}

// Permissions
const canEdit = (item: Asset) => {
  if (!currentUser) return false
  if (['Admin', 'Manager'].includes(currentUser.role)) return true
  return item.created_by === currentUser.id
}

const canDelete = () => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
}

// CRUD operations
const resetForm = () => {
  form.value = {
    wbs_id: wbsItems.value[0]?.id || 0,
    asset_code: '',
    asset_type: 'CAPEX',
    description: '',
    owner_group_id: groups.value[0]?.id || 0,
    status: 'Active'
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (item: Asset) => {
  selectedItem.value = item
  form.value = {
    wbs_id: item.wbs_id,
    asset_code: item.asset_code,
    asset_type: item.asset_type || 'CAPEX',
    description: item.description || '',
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
    if (!form.value.wbs_id) {
      showError('Please select a WBS')
      return
    }
    if (!form.value.asset_code.trim()) {
      showError('Asset Code is required')
      return
    }

    loading.value = true
    await useApiFetch('/assets', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
    success('Asset created successfully!')
  } catch (e: any) {
    showError(`Failed to create asset: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const updateItem = async () => {
  if (!selectedItem.value) return
  try {
    loading.value = true
    await useApiFetch(`/assets/${selectedItem.value.id}`, {
      method: 'PUT',
      body: {
        asset_code: form.value.asset_code,
        asset_type: form.value.asset_type,
        description: form.value.description,
        status: form.value.status
      }
    })
    await fetchItems()
    closeModals()
    success('Asset updated successfully!')
  } catch (e: any) {
    showError(`Failed to update asset: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const deleteItem = async (item: Asset) => {
  if (!confirm(`Are you sure you want to delete asset "${item.asset_code}"?`)) {
    return
  }
  try {
    loading.value = true
    await useApiFetch(`/assets/${item.id}`, { method: 'DELETE' })
    await fetchItems()
    success('Asset deleted successfully!')
  } catch (e: any) {
    showError(`Failed to delete asset: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const tableColumns = [
  { key: 'asset_code', label: 'Asset Code', sortable: true },
  { key: 'wbs', label: 'WBS', sortable: false },
  { key: 'asset_type', label: 'Type', sortable: true, align: 'center' as const },
  { key: 'description', label: 'Description', sortable: false },
  { key: 'owner_group', label: 'Owner Group', sortable: false },
  { key: 'status', label: 'Status', sortable: true, align: 'center' as const },
  { key: 'created_by', label: 'Created By', sortable: false },
  { key: 'actions', label: 'Actions', sortable: false }
]
</script>

<template>
  <BaseCard title="Assets" subtitle="Manage asset inventory and tracking">
    <template #header>
      <div class="header-actions">
        <BaseButton variant="primary" @click="openCreateModal">
          + Create Asset
        </BaseButton>
      </div>
    </template>

    <div class="filters">
      <BaseSelect
        v-model="filterStatus"
        :options="[{ value: null, label: 'All Statuses' }, ...statusOptions]"
        label="Status"
        @change="fetchItems"
      />
      <BaseSelect
        v-model="filterWBS"
        :options="[{ value: null, label: 'All WBS' }, ...wbsOptions]"
        label="WBS"
        @change="fetchItems"
      />
      <BaseSelect
        v-model="filterAssetType"
        :options="[{ value: null, label: 'All Types' }, ...assetTypeOptions]"
        label="Asset Type"
        @change="fetchItems"
      />
    </div>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" label="Loading assets..." />
    </div>

    <p v-else-if="error" class="error-message" role="alert">{{ error }}</p>

    <EmptyState
      v-else-if="filteredItems.length === 0"
      title="No assets found"
      description="Click 'Create Asset' to add your first asset."
      action-text="Create Asset"
      @action="openCreateModal"
    />

    <BaseTable
      v-else
      :columns="tableColumns"
      :data="filteredItems"
      :loading="loading"
      selectable
      sticky-header
      empty-message="No assets found"
      @row-click="openEditModal"
    >
      <template #cell-asset_code="{ value }">
        <code class="asset-code">{{ value }}</code>
      </template>

      <template #cell-wbs="{ row }">
        {{ getWBSCode(row.wbs_id) }}
      </template>

      <template #cell-asset_type="{ value }">
        <BaseBadge :variant="getAssetTypeVariant(value)" size="sm">
          {{ value || 'CAPEX' }}
        </BaseBadge>
      </template>

      <template #cell-description="{ value }">
        <span class="description">{{ value || '-' }}</span>
      </template>

      <template #cell-owner_group="{ row }">
        <BaseBadge variant="secondary" size="sm">
          {{ getGroupName(row.owner_group_id) }}
        </BaseBadge>
      </template>

      <template #cell-status="{ value }">
        <BaseBadge :variant="getStatusVariant(value)" size="sm">
          {{ value || 'Active' }}
        </BaseBadge>
      </template>

      <template #cell-created_by="{ value }">
        User #{{ value }}
      </template>

      <template #cell-actions="{ row }">
        <div class="action-buttons" v-if="canEdit(row) || canDelete()">
          <BaseButton
            v-if="canEdit(row)"
            size="sm"
            variant="secondary"
            @click="openEditModal(row)"
          >
            Edit
          </BaseButton>
          <BaseButton
            v-if="canDelete()"
            size="sm"
            variant="danger"
            @click="deleteItem(row)"
          >
            Delete
          </BaseButton>
        </div>
      </template>
    </BaseTable>

    <BaseModal v-model="showCreateModal" title="Create Asset" size="lg">
      <form @submit.prevent="createItem">
        <BaseSelect
          v-model="form.wbs_id"
          :options="wbsOptions"
          label="WBS"
          required
          help-text="Select the Work Breakdown Structure this asset belongs to"
        />

        <BaseInput
          v-model="form.asset_code"
          label="Asset Code"
          placeholder="e.g., ASSET-2025-001"
          required
        />

        <BaseSelect
          v-model="form.asset_type"
          :options="assetTypeOptions"
          label="Asset Type"
          required
        />

        <BaseTextarea
          v-model="form.description"
          label="Description"
          placeholder="Optional description"
          rows="3"
        />

        <BaseSelect
          v-model="form.status"
          :options="statusOptions"
          label="Status"
          required
        />

        <div class="form-note">
          <p>Owner Group will be automatically inherited from the selected WBS.</p>
        </div>
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="createItem">
          Create Asset
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal v-model="showEditModal" title="Edit Asset" size="lg">
      <form @submit.prevent="updateItem">
        <BaseInput
          :model-value="getWBSCode(form.wbs_id)"
          label="WBS"
          disabled
          help-text="Cannot change parent entity"
        />

        <BaseInput
          v-model="form.asset_code"
          label="Asset Code"
          required
        />

        <BaseSelect
          v-model="form.asset_type"
          :options="assetTypeOptions"
          label="Asset Type"
          required
        />

        <BaseTextarea
          v-model="form.description"
          label="Description"
          rows="3"
        />

        <BaseSelect
          v-model="form.status"
          :options="statusOptions"
          label="Status"
          required
        />

        <BaseInput
          :model-value="getGroupName(form.owner_group_id)"
          label="Owner Group (Inherited)"
          disabled
          help-text="Inherited from parent WBS"
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

.asset-code {
  font-family: monospace;
  background: var(--color-gray-100);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 600;
}

.description {
  font-size: var(--text-sm);
  color: var(--color-gray-500);
}

.action-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.form-note {
  padding: var(--spacing-3);
  background: var(--color-gray-50);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-gray-600);
}

.form-note p {
  margin: 0;
}

@media (max-width: 640px) {
  .filters {
    flex-direction: column;
  }
}
</style>
