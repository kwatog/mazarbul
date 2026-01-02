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

interface WBS {
  id: number
  business_case_line_item_id: number
  wbs_code: string
  description?: string
  owner_group_id: number
  status?: string
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface LineItem {
  id: number
  business_case_id: number
  budget_item_id: number
  title: string
  spend_category: string
}

interface Group {
  id: number
  name: string
}

const items = ref<WBS[]>([])
const lineItems = ref<LineItem[]>([])
const groups = ref<Group[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedItem = ref<WBS | null>(null)

const form = ref({
  business_case_line_item_id: 0,
  wbs_code: '',
  description: '',
  owner_group_id: 0,
  status: 'Active'
})

const filterStatus = ref<string | null>(null)
const filterLineItem = ref<number | null>(null)

const statuses = ['Active', 'Inactive', 'Closed']

const statusOptions = [
  { value: 'Active', label: 'Active' },
  { value: 'Inactive', label: 'Inactive' },
  { value: 'Closed', label: 'Closed' }
]

const lineItemOptions = computed(() =>
  lineItems.value.map(li => ({
    value: li.id,
    label: `${li.title} (${li.spend_category})`
  }))
)

const groupOptions = computed(() =>
  groups.value.map(g => ({ value: g.id, label: g.name }))
)

const fetchItems = async () => {
  try {
    loading.value = true
    const data = await useApiFetch('/wbs', { method: 'GET' })
    items.value = data as WBS[]
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load WBS items.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

const fetchLineItems = async () => {
  try {
    const data = await useApiFetch('/business-case-line-items', { method: 'GET' })
    lineItems.value = data as LineItem[]
  } catch (e: any) {
    console.error('Failed to fetch line items:', e)
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

const filteredItems = computed(() => {
  let result = items.value
  if (filterStatus.value) {
    result = result.filter(item => item.status === filterStatus.value)
  }
  if (filterLineItem.value) {
    result = result.filter(item => item.business_case_line_item_id === filterLineItem.value)
  }
  return result
})

const getLineItemTitle = (id: number) => {
  return lineItems.value.find(li => li.id === id)?.title || 'Unknown'
}

const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

const getStatusVariant = (status?: string): 'success' | 'secondary' | 'danger' => {
  const variants: Record<string, 'success' | 'secondary' | 'danger'> = {
    'Active': 'success',
    'Inactive': 'secondary',
    'Closed': 'danger'
  }
  return variants[status || 'Active'] || 'secondary'
}

const canEdit = (item: WBS) => {
  if (!currentUser) return false
  if (['Admin', 'Manager'].includes(currentUser.role)) return true
  return item.created_by === currentUser.id
}

const canDelete = () => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
}

const resetForm = () => {
  form.value = {
    business_case_line_item_id: 0,
    wbs_code: '',
    description: '',
    owner_group_id: 0,
    status: 'Active'
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (item: WBS) => {
  selectedItem.value = item
  form.value = {
    business_case_line_item_id: item.business_case_line_item_id,
    wbs_code: item.wbs_code,
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
    if (!form.value.business_case_line_item_id) {
      showError('Please select a line item')
      return
    }
    if (!form.value.wbs_code.trim()) {
      showError('WBS Code is required')
      return
    }

    loading.value = true
    await useApiFetch('/wbs', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
    success('WBS item created successfully!')
  } catch (e: any) {
    showError(`Failed to create WBS: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const updateItem = async () => {
  if (!selectedItem.value) return
  try {
    loading.value = true
    await useApiFetch(`/wbs/${selectedItem.value.id}`, {
      method: 'PUT',
      body: {
        wbs_code: form.value.wbs_code,
        description: form.value.description,
        status: form.value.status
      }
    })
    await fetchItems()
    closeModals()
    success('WBS item updated successfully!')
  } catch (e: any) {
    showError(`Failed to update WBS: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const deleteItem = async (item: WBS) => {
  if (!confirm(`Are you sure you want to delete WBS "${item.wbs_code}"?`)) return
  try {
    loading.value = true
    await useApiFetch(`/wbs/${item.id}`, { method: 'DELETE' })
    await fetchItems()
    success('WBS item deleted successfully!')
  } catch (e: any) {
    showError(`Failed to delete WBS: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const tableColumns = [
  { key: 'wbs_code', label: 'WBS Code', sortable: true },
  { key: 'line_item', label: 'Line Item', sortable: false },
  { key: 'description', label: 'Description', sortable: false },
  { key: 'owner_group', label: 'Owner Group', sortable: false },
  { key: 'status', label: 'Status', sortable: true, align: 'center' as const },
  { key: 'created_by', label: 'Created By', sortable: true },
  { key: 'actions', label: 'Actions', sortable: false }
]

onMounted(async () => {
  await fetchLineItems()
  await fetchGroups()
  await fetchItems()
})
</script>

<template>
  <BaseCard title="Work Breakdown Structure (WBS)" subtitle="Manage WBS items and assignments">
    <template #header>
      <div class="header-actions">
        <BaseButton variant="primary" @click="openCreateModal">
          + Create WBS
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
        v-model="filterLineItem"
        :options="[{ value: null, label: 'All Line Items' }, ...lineItemOptions]"
        label="Line Item"
        @change="fetchItems"
      />
    </div>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" label="Loading WBS items..." />
    </div>

    <p v-else-if="error" class="error-message">{{ error }}</p>

    <EmptyState
      v-else-if="filteredItems.length === 0"
      title="No WBS items found"
      description="Click 'Create WBS' to add your first work breakdown structure item."
      action-text="Create First WBS"
      @action="openCreateModal"
    />

    <BaseTable
      v-else
      :columns="tableColumns"
      :data="filteredItems"
      :loading="loading"
      selectable
      sticky-header
      empty-message="No WBS items found"
      @row-click="openEditModal"
    >
      <template #cell-wbs_code="{ value }">
        <code class="ref-code">{{ value }}</code>
      </template>

      <template #cell-line_item="{ row }">
        {{ getLineItemTitle(row.business_case_line_item_id) }}
      </template>

      <template #cell-description="{ value }">
        {{ value || '-' }}
      </template>

      <template #cell-owner_group="{ row }">
        <BaseBadge variant="primary" size="sm">{{ getGroupName(row.owner_group_id) }}</BaseBadge>
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

    <BaseModal v-model="showCreateModal" title="Create WBS" size="lg">
      <form @submit.prevent="createItem">
        <BaseSelect
          v-model="form.business_case_line_item_id"
          :options="[{ value: 0, label: 'Select a line item' }, ...lineItemOptions]"
          label="Line Item"
          required
          help-text="Select the parent business case line item"
        />

        <BaseInput
          v-model="form.wbs_code"
          label="WBS Code"
          placeholder="e.g., WBS-2025-001"
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

        <p class="info-note">
          <strong>Note:</strong> Owner Group will be automatically inherited from the selected Line Item.
        </p>
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="createItem">
          Create WBS
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal v-model="showEditModal" title="Edit WBS" size="lg">
      <form @submit.prevent="updateItem">
        <BaseInput
          :model-value="getLineItemTitle(form.business_case_line_item_id)"
          label="Line Item"
          disabled
          help-text="Cannot change parent entity"
        />

        <BaseInput
          v-model="form.wbs_code"
          label="WBS Code"
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
          help-text="Inherited from parent Line Item"
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

.ref-code {
  font-family: monospace;
  background: var(--color-gray-100);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}

.action-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.info-note {
  font-size: var(--text-sm);
  color: var(--color-gray-600);
  padding: var(--spacing-3);
  background: var(--color-gray-50);
  border-radius: var(--radius-md);
  margin-top: var(--spacing-4);
}

@media (max-width: 640px) {
  .filters {
    flex-direction: column;
  }
}
</style>
