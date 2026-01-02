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

interface ResourceAllocation {
  id: number
  resource_id: number
  po_id: number
  allocation_start?: string
  allocation_end?: string
  expected_monthly_burn?: string
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

const items = ref<ResourceAllocation[]>([])
const resources = ref<Resource[]>([])
const purchaseOrders = ref<PurchaseOrder[]>([])
const groups = ref<Group[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const filterResource = ref<number | null>(null)
const filterPO = ref<number | null>(null)

const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedItem = ref<ResourceAllocation | null>(null)

const form = ref({
  resource_id: 0,
  po_id: 0,
  allocation_start: '',
  allocation_end: '',
  expected_monthly_burn: '',
  owner_group_id: 0
})

const resourceOptions = computed(() =>
  resources.value.map(r => ({
    value: r.id,
    label: `${r.name}${r.vendor ? ' (' + r.vendor + ')' : ''}${r.role ? ' - ' + r.role : ''}`
  }))
)

const poOptions = computed(() =>
  purchaseOrders.value.map(po => ({
    value: po.id,
    label: `${po.po_number}${po.supplier ? ' - ' + po.supplier : ''}`
  }))
)

const groupOptions = computed(() =>
  groups.value.map(g => ({ value: g.id, label: g.name }))
)

const fetchResources = async () => {
  try {
    const data = await useApiFetch<Resource[]>('/resources')
    resources.value = data as any
  } catch (e: any) {
    console.error('Failed to fetch resources:', e)
  }
}

const fetchPurchaseOrders = async () => {
  try {
    const data = await useApiFetch<PurchaseOrder[]>('/purchase-orders')
    purchaseOrders.value = data as any
  } catch (e: any) {
    console.error('Failed to fetch purchase orders:', e)
  }
}

const fetchGroups = async () => {
  try {
    const data = await useApiFetch<Group[]>('/user-groups')
    groups.value = data as any
  } catch (e: any) {
    console.error('Failed to fetch groups:', e)
  }
}

const fetchItems = async () => {
  try {
    loading.value = true
    let url = '/allocations?limit=100'
    if (filterResource.value) {
      url += `&resource_id=${filterResource.value}`
    }
    if (filterPO.value) {
      url += `&po_id=${filterPO.value}`
    }
    const data = await useApiFetch<ResourceAllocation[]>(url)
    items.value = data as any
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load allocations.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchResources()
  await fetchPurchaseOrders()
  await fetchGroups()
  await fetchItems()
})

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

const canEdit = (item: ResourceAllocation) => {
  if (!currentUser) return false
  if (currentUser.role === 'Admin') return true
  if (currentUser.role === 'Manager') return true
  return item.created_by === currentUser.id
}

const canDelete = () => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
}

const canCreate = computed(() => {
  if (!currentUser) return false
  return ['Admin', 'Manager'].includes(currentUser.role)
})

const resetForm = () => {
  form.value = {
    resource_id: 0,
    po_id: 0,
    allocation_start: '',
    allocation_end: '',
    expected_monthly_burn: '',
    owner_group_id: 0
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (item: ResourceAllocation) => {
  selectedItem.value = item
  form.value = {
    resource_id: item.resource_id,
    po_id: item.po_id,
    allocation_start: item.allocation_start || '',
    allocation_end: item.allocation_end || '',
    expected_monthly_burn: item.expected_monthly_burn || '',
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
    if (!form.value.resource_id) {
      showError('Please select a resource')
      return
    }
    if (!form.value.po_id) {
      showError('Please select a purchase order')
      return
    }

    loading.value = true
    await useApiFetch('/allocations', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
    success('Resource allocation created successfully!')
  } catch (e: any) {
    showError(`Failed to create allocation: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const updateItem = async () => {
  if (!selectedItem.value) return
  try {
    loading.value = true
    await useApiFetch(`/allocations/${selectedItem.value.id}`, {
      method: 'PUT',
      body: {
        allocation_start: form.value.allocation_start,
        allocation_end: form.value.allocation_end,
        expected_monthly_burn: form.value.expected_monthly_burn
      }
    })
    await fetchItems()
    closeModals()
    success('Resource allocation updated successfully!')
  } catch (e: any) {
    showError(`Failed to update allocation: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const deleteItem = async (item: ResourceAllocation) => {
  if (!confirm(`Are you sure you want to delete this allocation?`)) {
    return
  }
  try {
    loading.value = true
    await useApiFetch(`/allocations/${item.id}`, { method: 'DELETE' })
    await fetchItems()
    success('Resource allocation deleted successfully!')
  } catch (e: any) {
    showError(`Failed to delete allocation: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const tableColumns = [
  { key: 'resource', label: 'Resource', sortable: true },
  { key: 'po_number', label: 'Purchase Order', sortable: true },
  { key: 'allocation_start', label: 'Start Date', sortable: true, align: 'center' as const },
  { key: 'allocation_end', label: 'End Date', sortable: true, align: 'center' as const },
  { key: 'expected_monthly_burn', label: 'Monthly Burn', sortable: true, align: 'right' as const },
  { key: 'owner_group', label: 'Owner Group', sortable: false },
  { key: 'actions', label: 'Actions', sortable: false }
]
</script>

<template>
  <BaseCard title="Resource Allocations" subtitle="Manage resource assignments to purchase orders">
    <template #header>
      <div class="header-actions">
        <BaseButton v-if="canCreate" variant="primary" @click="openCreateModal">
          + Create Allocation
        </BaseButton>
      </div>
    </template>

    <div class="filters">
      <BaseSelect
        v-model="filterResource"
        :options="[{ value: null, label: 'All Resources' }, ...resourceOptions]"
        label="Resource"
        @change="fetchItems"
      />
      <BaseSelect
        v-model="filterPO"
        :options="[{ value: null, label: 'All Purchase Orders' }, ...poOptions]"
        label="Purchase Order"
        @change="fetchItems"
      />
    </div>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" label="Loading allocations..." />
    </div>

    <p v-else-if="error" class="error-message">{{ error }}</p>

    <EmptyState
      v-else-if="filteredItems.length === 0"
      title="No allocations found"
      description="Click 'Create Allocation' to add your first resource allocation."
      :action-text="canCreate ? 'Create Allocation' : undefined"
      @action="openCreateModal"
    />

    <BaseTable
      v-else
      :columns="tableColumns"
      :data="filteredItems"
      :loading="loading"
      selectable
      sticky-header
      empty-message="No allocations found"
      @row-click="openEditModal"
    >
      <template #cell-resource="{ row }">
        <strong>{{ getResourceName(row.resource_id) }}</strong>
      </template>

      <template #cell-po_number="{ row }">
        <code class="ref-code">{{ getPONumber(row.po_id) }}</code>
      </template>

      <template #cell-allocation_start="{ row }">
        {{ formatDate(row.allocation_start) }}
      </template>

      <template #cell-allocation_end="{ row }">
        {{ formatDate(row.allocation_end) }}
      </template>

      <template #cell-expected_monthly_burn="{ row }">
        {{ formatCurrency(row.expected_monthly_burn, row.po_id) }}
      </template>

      <template #cell-owner_group="{ row }">
        <BaseBadge variant="primary" size="sm">{{ getGroupName(row.owner_group_id) }}</BaseBadge>
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

    <BaseModal v-model="showCreateModal" title="Create Resource Allocation" size="lg">
      <form @submit.prevent="createItem">
        <BaseSelect
          v-model="form.resource_id"
          :options="[{ value: 0, label: 'Select a resource' }, ...resourceOptions]"
          label="Resource"
          required
        />

        <BaseSelect
          v-model="form.po_id"
          :options="[{ value: 0, label: 'Select a purchase order' }, ...poOptions]"
          label="Purchase Order"
          required
        />

        <div class="form-row">
          <BaseInput
            v-model="form.allocation_start"
            label="Allocation Start"
            type="date"
          />
          <BaseInput
            v-model="form.allocation_end"
            label="Allocation End"
            type="date"
          />
        </div>

        <BaseInput
          v-model="form.expected_monthly_burn"
          label="Expected Monthly Burn"
          type="text"
          placeholder="0.00"
          help-text="Amount in PO currency"
        />

        <div class="info-box">
          <strong>Note:</strong> Owner Group will be automatically inherited from the selected Purchase Order.
        </div>
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="createItem">
          Create Allocation
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal v-model="showEditModal" title="Edit Resource Allocation" size="lg">
      <form @submit.prevent="updateItem">
        <BaseInput
          :model-value="getResourceName(form.resource_id)"
          label="Resource"
          disabled
          help-text="Cannot change resource after creation"
        />

        <BaseInput
          :model-value="getPONumber(form.po_id)"
          label="Purchase Order"
          disabled
          help-text="Cannot change purchase order after creation"
        />

        <div class="form-row">
          <BaseInput
            v-model="form.allocation_start"
            label="Allocation Start"
            type="date"
          />
          <BaseInput
            v-model="form.allocation_end"
            label="Allocation End"
            type="date"
          />
        </div>

        <BaseInput
          v-model="form.expected_monthly_burn"
          label="Expected Monthly Burn"
          type="text"
          placeholder="0.00"
          help-text="Amount in PO currency"
        />

        <BaseInput
          :model-value="getGroupName(form.owner_group_id)"
          label="Owner Group (Inherited)"
          disabled
          help-text="Inherited from parent Purchase Order"
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
}

.info-box {
  padding: var(--spacing-3);
  background: var(--color-info-50);
  border-left: 3px solid var(--color-info-500);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-gray-700);
  margin-top: var(--spacing-4);
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
