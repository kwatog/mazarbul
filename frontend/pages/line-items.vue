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

interface LineItem {
  id: number
  business_case_id: number
  budget_item_id: number
  owner_group_id: number
  title: string
  description?: string
  spend_category: string
  requested_amount: string
  currency: string
  planned_commit_date?: string
  status?: string
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

interface BusinessCase {
  id: number
  title: string
}

interface BudgetItem {
  id: number
  workday_ref: string
  title: string
}

interface UserGroup {
  id: number
  name: string
}

const items = ref<LineItem[]>([])
const businessCases = ref<BusinessCase[]>([])
const budgetItems = ref<BudgetItem[]>([])
const groups = ref<UserGroup[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const filterBusinessCase = ref<number | null>(null)
const filterSpendCategory = ref<string | null>(null)

const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedItem = ref<LineItem | null>(null)

const form = ref({
  business_case_id: 0,
  budget_item_id: 0,
  owner_group_id: 0,
  title: '',
  description: '',
  spend_category: 'OPEX',
  requested_amount: '',
  currency: 'USD',
  planned_commit_date: '',
  status: 'Draft'
})

const spendCategoryOptions = [
  { value: 'CAPEX', label: 'CAPEX' },
  { value: 'OPEX', label: 'OPEX' }
]

const statusOptions = [
  { value: 'Draft', label: 'Draft' },
  { value: 'Submitted', label: 'Submitted' },
  { value: 'Approved', label: 'Approved' },
  { value: 'Rejected', label: 'Rejected' },
  { value: 'Allocated', label: 'Allocated' }
]

const currencyOptions = [
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
  { value: 'GBP', label: 'GBP' }
]

const businessCaseOptions = computed(() => 
  businessCases.value.map(bc => ({ value: bc.id, label: bc.title }))
)

const budgetItemOptions = computed(() => 
  budgetItems.value.map(bi => ({ value: bi.id, label: `${bi.workday_ref} - ${bi.title}` }))
)

const groupOptions = computed(() => 
  groups.value.map(g => ({ value: g.id, label: g.name }))
)

const filterBusinessCaseOptions = computed(() => [
  { value: null as any, label: 'All Business Cases' },
  ...businessCaseOptions.value
])

const filterSpendCategoryOptions = computed(() => [
  { value: null as any, label: 'All Categories' },
  ...spendCategoryOptions
])

const fetchBusinessCases = async () => {
  try {
    const res = await useApiFetch<BusinessCase[]>('/business-cases?limit=100')
    businessCases.value = res as any
  } catch (e: any) {
    console.error('Failed to load business cases:', e)
  }
}

const fetchBudgetItems = async () => {
  try {
    const res = await useApiFetch<BudgetItem[]>('/budget-items?limit=100')
    budgetItems.value = res as any
  } catch (e: any) {
    console.error('Failed to load budget items:', e)
  }
}

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
    let url = '/business-case-line-items?limit=100'
    if (filterBusinessCase.value) {
      url += `&business_case_id=${filterBusinessCase.value}`
    }
    if (filterSpendCategory.value) {
      url += `&spend_category=${filterSpendCategory.value}`
    }
    const res = await useApiFetch<LineItem[]>(url)
    items.value = res as any
    error.value = null
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load line items.'
    if (e.response?.status === 401) {
      navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    business_case_id: businessCases.value[0]?.id || 0,
    budget_item_id: budgetItems.value[0]?.id || 0,
    owner_group_id: groups.value[0]?.id || 0,
    title: '',
    description: '',
    spend_category: 'OPEX',
    requested_amount: '',
    currency: 'USD',
    planned_commit_date: '',
    status: 'Draft'
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateModal.value = true
}

const openEditModal = (item: LineItem) => {
  selectedItem.value = item
  form.value = {
    business_case_id: item.business_case_id,
    budget_item_id: item.budget_item_id,
    owner_group_id: item.owner_group_id,
    title: item.title,
    description: item.description || '',
    spend_category: item.spend_category,
    requested_amount: item.requested_amount,
    currency: item.currency,
    planned_commit_date: item.planned_commit_date || '',
    status: item.status || 'Draft'
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
    loading.value = true
    await useApiFetch('/business-case-line-items', {
      method: 'POST',
      body: form.value
    })
    await fetchItems()
    closeModals()
    success('Line item created successfully!')
  } catch (e: any) {
    showError(`Failed to create line item: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const updateItem = async () => {
  if (!selectedItem.value) return
  try {
    loading.value = true
    await useApiFetch(`/business-case-line-items/${selectedItem.value.id}`, {
      method: 'PUT',
      body: {
        title: form.value.title,
        description: form.value.description,
        spend_category: form.value.spend_category,
        requested_amount: form.value.requested_amount,
        currency: form.value.currency,
        planned_commit_date: form.value.planned_commit_date,
        status: form.value.status
      }
    })
    await fetchItems()
    closeModals()
    success('Line item updated successfully!')
  } catch (e: any) {
    showError(`Failed to update line item: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const deleteItem = async (item: LineItem) => {
  if (!confirm(`Are you sure you want to delete line item "${item.title}"?`)) {
    return
  }
  try {
    loading.value = true
    await useApiFetch(`/business-case-line-items/${item.id}`, {
      method: 'DELETE'
    })
    await fetchItems()
    success('Line item deleted successfully!')
  } catch (e: any) {
    showError(`Failed to delete line item: ${e.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const canEdit = (item: LineItem) => {
  if (!currentUser) return false
  if (['Admin', 'Manager'].includes(currentUser.role)) return true
  return item.created_by === currentUser.id
}

const canDelete = () => {
  return currentUser && ['Admin', 'Manager'].includes(currentUser.role)
}

const formatCurrency = (amount: string | number, currency: string) => {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(num)
}

const getBusinessCaseTitle = (id: number) => {
  return businessCases.value.find(bc => bc.id === id)?.title || 'Unknown'
}

const getBudgetItemRef = (id: number) => {
  return budgetItems.value.find(bi => bi.id === id)?.workday_ref || 'Unknown'
}

const getGroupName = (id: number) => {
  return groups.value.find(g => g.id === id)?.name || 'Unknown'
}

const tableColumns = [
  { key: 'title', label: 'Title', sortable: true },
  { key: 'business_case', label: 'Business Case', sortable: false },
  { key: 'budget_item', label: 'Budget Item', sortable: false },
  { key: 'spend_category', label: 'Category', sortable: true, align: 'center' as const },
  { key: 'requested_amount', label: 'Requested Amount', sortable: true, align: 'right' as const },
  { key: 'owner_group', label: 'Owner Group', sortable: false },
  { key: 'status', label: 'Status', sortable: true, align: 'center' as const },
  { key: 'actions', label: 'Actions', sortable: false }
]

onMounted(async () => {
  await Promise.all([
    fetchBusinessCases(),
    fetchBudgetItems(),
    fetchGroups()
  ])
  await fetchItems()
})
</script>

<template>
  <BaseCard title="Business Case Line Items" subtitle="Link business cases to budget items and allocate funds">
    <template #header>
      <div class="header-actions">
        <BaseButton variant="primary" @click="openCreateModal">
          + Create Line Item
        </BaseButton>
      </div>
    </template>

    <div class="filters">
      <BaseSelect
        v-model="filterBusinessCase"
        :options="filterBusinessCaseOptions"
        label="Business Case"
        @change="fetchItems"
      />
      <BaseSelect
        v-model="filterSpendCategory"
        :options="filterSpendCategoryOptions"
        label="Spend Category"
        @change="fetchItems"
      />
    </div>

    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" label="Loading line items..." />
    </div>

    <p v-else-if="error" class="error-message">{{ error }}</p>

    <EmptyState
      v-else-if="items.length === 0"
      title="No line items found"
      description="Click 'Create Line Item' to add one."
      action-text="Create Line Item"
      @action="openCreateModal"
    />

    <BaseTable
      v-else
      :columns="tableColumns"
      :data="items"
      :loading="loading"
      selectable
      sticky-header
      empty-message="No line items found"
      @row-click="openEditModal"
    >
      <template #cell-title="{ row, value }">
        <div>
          <strong>{{ value }}</strong>
          <div v-if="row.description" class="description">{{ row.description }}</div>
        </div>
      </template>

      <template #cell-business_case="{ row }">
        {{ getBusinessCaseTitle(row.business_case_id) }}
      </template>

      <template #cell-budget_item="{ row }">
        <code class="ref-code">{{ getBudgetItemRef(row.budget_item_id) }}</code>
      </template>

      <template #cell-spend_category="{ value }">
        <BaseBadge
          :variant="value === 'CAPEX' ? 'primary' : 'info'"
          size="sm"
        >
          {{ value }}
        </BaseBadge>
      </template>

      <template #cell-requested_amount="{ value, row }">
        {{ formatCurrency(value, row.currency) }}
      </template>

      <template #cell-owner_group="{ row }">
        <BaseBadge variant="secondary" size="sm">
          {{ getGroupName(row.owner_group_id) }}
        </BaseBadge>
      </template>

      <template #cell-status="{ value }">
        <BaseBadge
          :variant="value === 'Approved' ? 'success' : value === 'Rejected' ? 'danger' : 'warning'"
          size="sm"
        >
          {{ value || 'Draft' }}
        </BaseBadge>
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

    <BaseModal v-model="showCreateModal" title="Create Line Item" size="lg">
      <form @submit.prevent="createItem">
        <BaseSelect
          v-model.number="form.business_case_id"
          :options="businessCaseOptions"
          label="Business Case"
          required
        />

        <BaseSelect
          v-model.number="form.budget_item_id"
          :options="budgetItemOptions"
          label="Budget Item"
          required
        />

        <BaseSelect
          v-model.number="form.owner_group_id"
          :options="groupOptions"
          label="Owner Group"
          required
        >
          <template #help-text>
            This group will own all child records (WBS, Assets, POs, etc.)
          </template>
        </BaseSelect>

        <BaseInput
          v-model="form.title"
          label="Title"
          placeholder="e.g., AWS EC2 Infrastructure"
          required
        />

        <BaseTextarea
          v-model="form.description"
          label="Description"
          placeholder="Optional description"
          rows="3"
        />

        <div class="form-row">
          <BaseSelect
            v-model="form.spend_category"
            :options="spendCategoryOptions"
            label="Spend Category"
            required
          />
          <BaseSelect
            v-model="form.status"
            :options="statusOptions"
            label="Status"
            required
          />
        </div>

        <div class="form-row">
          <BaseInput
            v-model="form.requested_amount"
            label="Requested Amount"
            placeholder="0.00"
            required
          />
          <BaseSelect
            v-model="form.currency"
            :options="currencyOptions"
            label="Currency"
            required
          />
        </div>

        <BaseInput
          v-model="form.planned_commit_date"
          label="Planned Commit Date"
          type="date"
        />
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="createItem">
          Create Line Item
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal v-model="showEditModal" title="Edit Line Item" size="lg">
      <form @submit.prevent="updateItem">
        <BaseInput
          v-model="form.title"
          label="Title"
          required
        />

        <BaseTextarea
          v-model="form.description"
          label="Description"
          rows="3"
        />

        <div class="form-row">
          <BaseSelect
            v-model="form.spend_category"
            :options="spendCategoryOptions"
            label="Spend Category"
            required
          />
          <BaseSelect
            v-model="form.status"
            :options="statusOptions"
            label="Status"
            required
          />
        </div>

        <div class="form-row">
          <BaseInput
            v-model="form.requested_amount"
            label="Requested Amount"
            required
          />
          <BaseSelect
            v-model="form.currency"
            :options="currencyOptions"
            label="Currency"
            required
          />
        </div>

        <BaseInput
          v-model="form.planned_commit_date"
          label="Planned Commit Date"
          type="date"
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

.description {
  font-size: var(--text-sm);
  color: var(--color-gray-500);
  margin-top: var(--spacing-1);
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
