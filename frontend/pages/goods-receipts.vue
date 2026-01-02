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

interface GoodsReceipt {
  id: number
  po_id: number
  gr_number: string
  gr_date?: string
  amount: string
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
  total_amount: string
  currency: string
}

interface Group {
  id: number
  name: string
}

const items = ref<GoodsReceipt[]>([])
const purchaseOrders = ref<PurchaseOrder[]>([])
const groups = ref<Group[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const filterPO = ref<number | null>(null)

const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedItem = ref<GoodsReceipt | null>(null)

const form = ref({
  po_id: 0,
  gr_number: '',
  gr_date: new Date().toISOString().split('T')[0],
  amount: '',
  description: '',
  owner_group_id: 0
})

const purchaseOrderOptions = computed(() =>
  purchaseOrders.value.map(po => ({
    value: po.id,
    label: `${po.po_number}${po.supplier ? ' - ' + po.supplier : ''} (${po.currency} ${po.total_amount})`
  }))
)

const purchaseOrderFilterOptions = computed(() => [
  { value: null, label: 'All Purchase Orders' },
  ...purchaseOrders.value.map(po => ({
    value: po.id,
    label: `${po.po_number}${po.supplier ? ' - ' + po.supplier : ''}`
  }))
])

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
    const data = await useApiFetch<Group[]>('/groups')
    groups.value = data as any
  } catch (e: any) {
    console.error('Failed to fetch groups:', e)
  }
}

const fetchItems = async () => {
  try {
    loading.value = true
    let url = '/goods-receipts'
    const data = await useApiFetch<GoodsReceipt[]>(url)
    items.value = data as any
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load goods receipts.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

const filteredItems = computed(() => {
  let result = items.value
  if (filterPO.value) {
    result = result.filter(item => item.po_id === filterPO.value)
  }
  return result
})

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

const canEdit = (item: GoodsReceipt) => {
  if (!currentUser) return false
  if (['Admin', 'Manager'].includes(currentUser.role)) return true
  return item.created_by === currentUser.id
}

const canDelete = () => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
}

const resetForm = () => {
  form.value = {
    po_id: 0,
    gr_number: '',
    gr_date: new Date().toISOString().split('T')[0],
    amount: '',
    description: '',
    owner_group_id: 0
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (item: GoodsReceipt) => {
  selectedItem.value = item
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
  selectedItem.value = null
  resetForm()
}

const createItem = async () => {
  try {
    if (!form.value.po_id) {
      showError('Please select a purchase order')
      return
    }
    if (!form.value.gr_number.trim()) {
      showError('GR Number is required')
      return
    }
    if (!form.value.amount || parseFloat(form.value.amount) <= 0) {
      showError('Amount must be greater than 0')
      return
    }

    loading.value = true
    await useApiFetch('/goods-receipts', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
    success('Goods receipt created successfully!')
  } catch (e: any) {
    showError(`Failed to create goods receipt: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const updateItem = async () => {
  if (!selectedItem.value) return
  try {
    loading.value = true
    await useApiFetch(`/goods-receipts/${selectedItem.value.id}`, {
      method: 'PUT',
      body: {
        gr_date: form.value.gr_date,
        amount: form.value.amount,
        description: form.value.description
      }
    })
    await fetchItems()
    closeModals()
    success('Goods receipt updated successfully!')
  } catch (e: any) {
    showError(`Failed to update goods receipt: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const deleteItem = async (item: GoodsReceipt) => {
  if (!confirm(`Are you sure you want to delete goods receipt "${item.gr_number}"?`)) {
    return
  }
  try {
    loading.value = true
    await useApiFetch(`/goods-receipts/${item.id}`, { method: 'DELETE' })
    await fetchItems()
    success('Goods receipt deleted successfully!')
  } catch (e: any) {
    showError(`Failed to delete goods receipt: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const tableColumns = [
  { key: 'gr_number', label: 'GR Number', sortable: true },
  { key: 'po_number', label: 'Purchase Order', sortable: false },
  { key: 'gr_date', label: 'GR Date', sortable: true, align: 'center' as const },
  { key: 'amount', label: 'Amount', sortable: true, align: 'right' as const },
  { key: 'description', label: 'Description', sortable: false },
  { key: 'owner_group', label: 'Owner Group', sortable: false },
  { key: 'created_by', label: 'Created By', sortable: false },
  { key: 'actions', label: 'Actions', sortable: false }
]

onMounted(async () => {
  await fetchPurchaseOrders()
  await fetchGroups()
  await fetchItems()
})
</script>

<template>
  <BaseCard title="Goods Receipts" subtitle="Manage goods receipt records linked to purchase orders">
    <template #header>
      <div class="header-actions">
        <BaseButton variant="primary" @click="openCreateModal">
          + Create GR
        </BaseButton>
      </div>
    </template>

    <div class="filters">
      <BaseSelect
        v-model="filterPO"
        :options="purchaseOrderFilterOptions"
        label="Purchase Order"
      />
    </div>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" label="Loading goods receipts..." />
    </div>

    <p v-else-if="error" class="error-message">{{ error }}</p>

    <EmptyState
      v-else-if="filteredItems.length === 0"
      title="No goods receipts found"
      description="Click 'Create GR' to add your first goods receipt."
      action-text="Create First Goods Receipt"
      @action="openCreateModal"
    />

    <BaseTable
      v-else
      :columns="tableColumns"
      :data="filteredItems"
      :loading="loading"
      selectable
      sticky-header
      empty-message="No goods receipts found"
      @row-click="openEditModal"
    >
      <template #cell-gr_number="{ value }">
        <code class="ref-code">{{ value }}</code>
      </template>

      <template #cell-po_number="{ row }">
        {{ getPONumber(row.po_id) }}
      </template>

      <template #cell-gr_date="{ value }">
        <BaseBadge variant="secondary" size="sm">{{ formatDate(value) }}</BaseBadge>
      </template>

      <template #cell-amount="{ value, row }">
        {{ formatCurrency(value, row.po_id) }}
      </template>

      <template #cell-description="{ value }">
        {{ value || '-' }}
      </template>

      <template #cell-owner_group="{ row }">
        <BaseBadge variant="primary" size="sm">{{ getGroupName(row.owner_group_id) }}</BaseBadge>
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

    <BaseModal v-model="showCreateModal" title="Create Goods Receipt" size="lg">
      <form @submit.prevent="createItem">
        <BaseSelect
          v-model="form.po_id"
          :options="[{ value: 0, label: 'Select a purchase order' }, ...purchaseOrderOptions]"
          label="Purchase Order"
          required
        />

        <BaseInput
          v-model="form.gr_number"
          label="GR Number"
          placeholder="e.g., GR-2025-001"
          required
        />

        <BaseInput
          v-model="form.gr_date"
          label="GR Date"
          type="date"
          required
        />

        <BaseInput
          v-model="form.amount"
          label="Amount"
          placeholder="0.00"
          required
        />

        <BaseTextarea
          v-model="form.description"
          label="Description"
          placeholder="Optional description"
          rows="3"
        />

        <div class="info-notice">
          <strong>Note:</strong> Owner Group will be automatically inherited from the selected Purchase Order.
        </div>
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="createItem">
          Create Goods Receipt
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal v-model="showEditModal" title="Edit Goods Receipt" size="lg">
      <form @submit.prevent="updateItem">
        <BaseInput
          :model-value="getPONumber(form.po_id)"
          label="Purchase Order"
          disabled
          help-text="Cannot change parent entity"
        />

        <BaseInput
          v-model="form.gr_number"
          label="GR Number"
          disabled
          help-text="Cannot change GR number"
        />

        <BaseInput
          v-model="form.gr_date"
          label="GR Date"
          type="date"
        />

        <BaseInput
          v-model="form.amount"
          label="Amount"
          required
        />

        <BaseTextarea
          v-model="form.description"
          label="Description"
          rows="3"
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

.info-notice {
  padding: var(--spacing-3);
  background: var(--color-gray-50);
  border-left: 3px solid var(--color-primary);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--color-gray-600);
  margin-top: var(--spacing-4);
}

@media (max-width: 640px) {
  .filters {
    flex-direction: column;
  }
}
</style>
