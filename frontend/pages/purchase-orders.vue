<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.apiBase || config.public.apiBase
const token = useCookie('access_token')
const userInfo = useCookie('user_info')

// Parse user info to check role
const currentUser = userInfo.value ? JSON.parse(userInfo.value as string) : null

interface PurchaseOrder {
  id: number
  po_number: string
  supplier?: string
  total_amount: number
  currency: string
  status?: string
  created_by?: number
}

const pos = ref<PurchaseOrder[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Access modal state
const showAccessModal = ref(false)
const selectedPO = ref<PurchaseOrder | null>(null)

const fetchPOs = async () => {
  try {
    const res = await useApiFetch<PurchaseOrder[]>(`/purchase-orders`)
    pos.value = res as any
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

const canShareAccess = (po: PurchaseOrder) => {
  // Admin and Manager can always share
  if (currentUser && ['Admin', 'Manager'].includes(currentUser.role)) {
    return true
  }
  // Creator can share their own records
  return po.created_by === currentUser?.id
}

const openAccessModal = (po: PurchaseOrder) => {
  selectedPO.value = po
  showAccessModal.value = true
}

const closeAccessModal = () => {
  showAccessModal.value = false
  selectedPO.value = null
}

onMounted(fetchPOs)
</script>

<template>
  <section class="card">
    <h1 class="card-title">Purchase Orders</h1>
    <p class="card-sub">List of all POs from the backend API.</p>

    <p v-if="loading">Loading…</p>
    <p v-else-if="error" style="color: #cc0000;">{{ error }}</p>
    <table v-else class="po-table" style="width:100%; border-collapse:collapse; font-size:0.9rem;">
      <thead>
        <tr>
          <th style="text-align:left; padding:0.5rem 0;">PO Number</th>
          <th style="text-align:left; padding:0.5rem 0;">Supplier</th>
          <th style="text-align:left; padding:0.5rem 0;">Amount</th>
          <th style="text-align:left; padding:0.5rem 0;">Status</th>
          <th style="text-align:left; padding:0.5rem 0;">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="po in pos" :key="po.id">
          <td style="padding:0.4rem 0;">{{ po.po_number }}</td>
          <td style="padding:0.4rem 0;">{{ po.supplier || '-' }}</td>
          <td style="padding:0.4rem 0;">
            {{ po.total_amount }} {{ po.currency }}
          </td>
          <td style="padding:0.4rem 0;">{{ po.status || 'Open' }}</td>
          <td style="padding:0.4rem 0;">
            <button 
              v-if="canShareAccess(po)"
              @click="openAccessModal(po)"
              class="btn-share"
              title="Manage Access"
            >
              🔗 Share
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <!-- Record Access Modal -->
    <RecordAccessModal
      v-if="selectedPO"
      :record-type="'PurchaseOrder'"
      :record-id="selectedPO.id"
      :is-open="showAccessModal"
      @close="closeAccessModal"
      @updated="fetchPOs"
    />
  </section>
</template>

<style scoped>
.btn-share {
  background-color: var(--color-primary);
  color: white;
  border: none;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-share:hover {
  background-color: #17c653;
}

.po-table th,
.po-table td {
  vertical-align: middle;
}
</style>
