<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const userCookie = useCookie('user_info')
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

const user = decodeUserInfo(userCookie.value)

interface PurchaseOrder {
  id: number
  asset_id: number
  po_number: string
  ariba_pr_number?: string
  supplier?: string
  po_type?: string
  start_date?: string
  end_date?: string
  total_amount: string
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

const items = ref<PurchaseOrder[]>([])
const assets = ref<Asset[]>([])
const groups = ref<Group[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

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
const filterStatus = ref<string | null>(null)
const filterAsset = ref<number | null>(null)
const filterSpendCategory = ref<string | null>(null)
const filterSupplier = ref('')

const statuses = ['Open', 'Approved', 'In Progress', 'Completed', 'Cancelled']
const spendCategories = ['CAPEX', 'OPEX']
const poTypes = ['Standard', 'Contract', 'Blanket', 'Services']
const currencies = ['USD', 'EUR', 'GBP']

const statusOptions = [
  { value: null, label: 'All Statuses' },
  ...statuses.map(s => ({ value: s, label: s }))
]

const assetOptions = computed(() => [
  { value: null, label: 'All Assets' },
  ...assets.value.map(a => ({ value: a.id, label: a.asset_code }))
])

const spendCategoryOptions = [
  { value: null, label: 'All Categories' },
  ...spendCategories.map(sc => ({ value: sc, label: sc }))
]

const assetSelectOptions = computed(() =>
  assets.value.map(a => ({ value: a.id, label: a.asset_code }))
)

const currencyOptions = currencies.map(c => ({ value: c, label: c }))
const poTypeOptions = [
  { value: '', label: 'Select type' },
  ...poTypes.map(pt => ({ value: pt, label: pt }))
]

const spendCategorySelectOptions = spendCategories.map(sc => ({ value: sc, label: sc }))
const statusSelectOptions = statuses.map(s => ({ value: s, label: s }))

// Fetch data
const fetchItems = async () => {
  try {
    loading.value = true
    const data = await useApiFetch('/purchase-orders', { method: 'GET' })
    items.value = data as PurchaseOrder[]
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load purchase orders.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
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

onMounted(async () => {
  await fetchAssets()
  await fetchGroups()
  await fetchItems()
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

const getStatusVariant = (status?: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' | 'secondary' => {
  const variants: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger' | 'secondary'> = {
    'Open': 'primary',
    'Approved': 'success',
    'In Progress': 'warning',
    'Completed': 'info',
    'Cancelled': 'danger'
  }
  return variants[status || 'Open'] || 'secondary'
}

const getSpendCategoryVariant = (category?: string): 'primary' | 'info' => {
  return category === 'CAPEX' ? 'info' : 'primary'
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
  if (!user) return false
  if (user.role === 'Admin') return true
  if (user.role === 'Manager') return true
  return item.created_by === user.id
}

const canDelete = (item: PurchaseOrder) => {
  if (!user) return false
  if (user.role === 'Admin') return true
  if (user.role === 'Manager') return true
  return false
}

const canShareAccess = (item: PurchaseOrder) => {
  if (!user) return false
  if (['Admin', 'Manager'].includes(user.role)) return true
  return item.created_by === user.id
}

// CRUD operations
const resetForm = () => {
  form.value = {
    asset_id: assets.value[0]?.id || 0,
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
}

const openCreateModal = () => {
  resetForm()
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
  resetForm()
}

const createItem = async () => {
  try {
    if (!form.value.asset_id) {
      showError('Please select an asset')
      return
    }
    if (!form.value.po_number.trim()) {
      showError('PO Number is required')
      return
    }
    if (!form.value.total_amount || parseFloat(form.value.total_amount) <= 0) {
      showError('Total Amount must be greater than 0')
      return
    }

    loading.value = true
    await useApiFetch('/purchase-orders', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
    success('Purchase order created successfully!')
  } catch (e: any) {
    showError(`Failed to create purchase order: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const updateItem = async () => {
  if (!editingItem.value) return
  try {
    loading.value = true
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
    success('Purchase order updated successfully!')
  } catch (e: any) {
    showError(`Failed to update purchase order: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const deleteItem = async (item: PurchaseOrder) => {
  if (!confirm(`Are you sure you want to delete PO "${item.po_number}"?`)) return
  try {
    loading.value = true
    await useApiFetch(`/purchase-orders/${item.id}`, { method: 'DELETE' })
    await fetchItems()
    success('Purchase order deleted successfully!')
  } catch (e: any) {
    showError(`Failed to delete purchase order: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const tableColumns = [
  { key: 'po_number', label: 'PO Number', sortable: true },
  { key: 'asset', label: 'Asset', sortable: false },
  { key: 'supplier', label: 'Supplier', sortable: true },
  { key: 'total_amount', label: 'Amount', sortable: true, align: 'right' as const },
  { key: 'spend_category', label: 'Category', sortable: true, align: 'center' as const },
  { key: 'status', label: 'Status', sortable: true, align: 'center' as const },
  { key: 'owner_group', label: 'Owner Group', sortable: false },
  { key: 'actions', label: 'Actions', sortable: false }
]
</script>

<template>
  <BaseCard title="Purchase Orders" subtitle="Manage purchase orders and procurement">
    <template #header>
      <div class="header-actions">
        <BaseButton variant="primary" @click="openCreateModal">
          + Create PO
        </BaseButton>
      </div>
    </template>

    <div class="filters">
      <BaseSelect
        v-model="filterStatus"
        :options="statusOptions"
        label="Status"
        @change="fetchItems"
      />
      <BaseSelect
        v-model="filterAsset"
        :options="assetOptions"
        label="Asset"
        @change="fetchItems"
      />
      <BaseSelect
        v-model="filterSpendCategory"
        :options="spendCategoryOptions"
        label="Spend Category"
        @change="fetchItems"
      />
      <BaseInput
        v-model="filterSupplier"
        label="Supplier"
        placeholder="Search supplier..."
      />
    </div>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" label="Loading purchase orders..." />
    </div>

    <p v-else-if="error" class="error-message">{{ error }}</p>

    <EmptyState
      v-else-if="filteredItems.length === 0"
      title="No purchase orders found"
      description="Click 'Create PO' to add your first purchase order."
      action-text="Create PO"
      @action="openCreateModal"
    />

    <BaseTable
      v-else
      :columns="tableColumns"
      :data="filteredItems"
      :loading="loading"
      selectable
      sticky-header
      empty-message="No purchase orders found"
    >
      <template #cell-po_number="{ value }">
        <strong>{{ value }}</strong>
      </template>

      <template #cell-asset="{ row }">
        {{ getAssetCode(row.asset_id) }}
      </template>

      <template #cell-supplier="{ value }">
        {{ value || '-' }}
      </template>

      <template #cell-total_amount="{ value, row }">
        {{ formatCurrency(value, row.currency) }}
      </template>

      <template #cell-spend_category="{ value }">
        <BaseBadge :variant="getSpendCategoryVariant(value)" size="sm">
          {{ value }}
        </BaseBadge>
      </template>

      <template #cell-status="{ value }">
        <BaseBadge :variant="getStatusVariant(value)" size="sm">
          {{ value || 'Open' }}
        </BaseBadge>
      </template>

      <template #cell-owner_group="{ row }">
        <BaseBadge variant="secondary" size="sm">
          {{ getGroupName(row.owner_group_id) }}
        </BaseBadge>
      </template>

      <template #cell-actions="{ row }">
        <div class="action-buttons">
          <BaseButton
            v-if="canEdit(row)"
            size="sm"
            variant="secondary"
            @click="openEditModal(row)"
          >
            Edit
          </BaseButton>
          <BaseButton
            v-if="canDelete(row)"
            size="sm"
            variant="danger"
            @click="deleteItem(row)"
          >
            Delete
          </BaseButton>
          <BaseButton
            v-if="canShareAccess(row)"
            size="sm"
            variant="success"
            @click="openAccessModal(row)"
          >
            Share
          </BaseButton>
        </div>
      </template>
    </BaseTable>

    <!-- Create Modal -->
    <BaseModal v-model="showCreateModal" title="Create Purchase Order" size="lg">
      <form @submit.prevent="createItem">
        <div class="form-row">
          <BaseSelect
            v-model="form.asset_id"
            :options="assetSelectOptions"
            label="Asset"
            required
          />
          <BaseInput
            v-model="form.po_number"
            label="PO Number"
            placeholder="e.g., PO-2025-001"
            required
          />
        </div>

        <div class="form-row">
          <BaseInput
            v-model="form.ariba_pr_number"
            label="Ariba PR Number"
            placeholder="Optional"
          />
          <BaseInput
            v-model="form.supplier"
            label="Supplier"
            placeholder="Supplier name"
          />
        </div>

        <div class="form-row">
          <BaseSelect
            v-model="form.po_type"
            :options="poTypeOptions"
            label="PO Type"
          />
          <BaseSelect
            v-model="form.spend_category"
            :options="spendCategorySelectOptions"
            label="Spend Category"
            required
          />
        </div>

        <div class="form-row-triple">
          <BaseInput
            v-model="form.total_amount"
            label="Total Amount"
            type="text"
            placeholder="0.00"
            required
          />
          <BaseSelect
            v-model="form.currency"
            :options="currencyOptions"
            label="Currency"
            required
          />
          <BaseSelect
            v-model="form.status"
            :options="statusSelectOptions"
            label="Status"
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
            v-model="form.planned_commit_date"
            label="Planned Commit Date"
            type="date"
          />
          <BaseInput
            v-model="form.actual_commit_date"
            label="Actual Commit Date"
            type="date"
          />
        </div>

        <div class="help-text">
          <strong>Note:</strong> Owner Group will be automatically inherited from the selected Asset.
        </div>
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="createItem">
          Create Purchase Order
        </BaseButton>
      </template>
    </BaseModal>

    <!-- Edit Modal -->
    <BaseModal v-model="showEditModal" title="Edit Purchase Order" size="lg">
      <form @submit.prevent="updateItem">
        <div class="form-row">
          <BaseInput
            :model-value="getAssetCode(form.asset_id)"
            label="Asset"
            disabled
            help-text="Cannot change parent entity"
          />
          <BaseInput
            :model-value="form.po_number"
            label="PO Number"
            disabled
            help-text="Cannot change PO number"
          />
        </div>

        <div class="form-row">
          <BaseInput
            v-model="form.ariba_pr_number"
            label="Ariba PR Number"
          />
          <BaseInput
            v-model="form.supplier"
            label="Supplier"
          />
        </div>

        <div class="form-row">
          <BaseSelect
            v-model="form.po_type"
            :options="poTypeOptions"
            label="PO Type"
          />
          <BaseSelect
            v-model="form.spend_category"
            :options="spendCategorySelectOptions"
            label="Spend Category"
            required
          />
        </div>

        <div class="form-row-triple">
          <BaseInput
            v-model="form.total_amount"
            label="Total Amount"
            type="text"
            required
          />
          <BaseSelect
            v-model="form.currency"
            :options="currencyOptions"
            label="Currency"
            required
          />
          <BaseSelect
            v-model="form.status"
            :options="statusSelectOptions"
            label="Status"
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
            v-model="form.planned_commit_date"
            label="Planned Commit Date"
            type="date"
          />
          <BaseInput
            v-model="form.actual_commit_date"
            label="Actual Commit Date"
            type="date"
          />
        </div>

        <BaseInput
          :model-value="getGroupName(form.owner_group_id)"
          label="Owner Group (Inherited)"
          disabled
          help-text="Inherited from parent Asset"
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

    <!-- Record Access Modal -->
    <RecordAccessModal
      v-if="selectedPO"
      :record-type="'PurchaseOrder'"
      :record-id="selectedPO.id"
      :is-open="showAccessModal"
      @close="closeModals"
      @updated="fetchItems"
    />
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

.form-row-triple {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--spacing-4);
}

.help-text {
  font-size: var(--text-sm);
  color: var(--color-gray-500);
  padding: var(--spacing-3);
  background: var(--color-gray-50);
  border-radius: var(--radius-md);
  margin-top: var(--spacing-2);
}

@media (max-width: 768px) {
  .filters {
    flex-direction: column;
  }

  .form-row,
  .form-row-triple {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .action-buttons {
    flex-direction: column;
  }
}
</style>
