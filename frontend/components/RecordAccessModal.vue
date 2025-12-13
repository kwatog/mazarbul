<script setup lang="ts">
interface Props {
  recordType: string
  recordId: number
  isOpen: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'updated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const config = useRuntimeConfig()
const apiBase = config.apiBase || config.public.apiBase
const token = useCookie('access_token')

interface RecordAccess {
  id: number
  record_type: string
  record_id: number
  user_id?: number
  group_id?: number
  access_level: string
  granted_by?: number
  granted_at?: string
  expires_at?: string
}

interface User {
  id: number
  username: string
  full_name: string
  role: string
}

interface UserGroup {
  id: number
  name: string
  description?: string
}

const accesses = ref<RecordAccess[]>([])
const users = ref<User[]>([])
const groups = ref<UserGroup[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Form for granting new access
const newAccess = ref({
  user_id: null as number | null,
  group_id: null as number | null,
  access_level: 'Read' as string,
  expires_at: '' as string
})

const showGrantForm = ref(false)

const fetchRecordAccess = async () => {
  if (!props.recordId) return
  
  try {
    loading.value = true
    const res = await useApiFetch<RecordAccess[]>(`/record-access/${props.recordType}/${props.recordId}`)
    accesses.value = res
  } catch (e: any) {
    error.value = 'Failed to load access permissions'
  } finally {
    loading.value = false
  }
}

const fetchUsers = async () => {
  try {
    const res = await useApiFetch<User[]>(`/users`)
    users.value = res
  } catch (e: any) {
    console.error('Failed to load users:', e)
  }
}

const fetchGroups = async () => {
  try {
    const res = await useApiFetch<UserGroup[]>(`/user-groups`)
    groups.value = res
  } catch (e: any) {
    console.error('Failed to load groups:', e)
  }
}

const grantAccess = async () => {
  try {
    const payload = {
      record_type: props.recordType,
      record_id: props.recordId,
      access_level: newAccess.value.access_level,
      user_id: newAccess.value.user_id,
      group_id: newAccess.value.group_id,
      expires_at: newAccess.value.expires_at || null
    }

    await useApiFetch(`/record-access`, { method: 'POST', body: payload })
    
    // Reset form
    newAccess.value = {
      user_id: null,
      group_id: null,
      access_level: 'Read',
      expires_at: ''
    }
    showGrantForm.value = false
    
    await fetchRecordAccess()
    emit('updated')
  } catch (e: any) {
    error.value = e.data?.detail || 'Failed to grant access'
  }
}

const revokeAccess = async (accessId: number) => {
  try {
    await useApiFetch(`/record-access/${accessId}`, { method: 'DELETE' })
    
    await fetchRecordAccess()
    emit('updated')
  } catch (e: any) {
    error.value = e.data?.detail || 'Failed to revoke access'
  }
}

const getUserById = (userId: number) => {
  return users.value.find(u => u.id === userId)
}

const getGroupById = (groupId: number) => {
  return groups.value.find(g => g.id === groupId)
}

const getAccessLevelColor = (level: string) => {
  switch (level) {
    case 'Read': return '#3b82f6'
    case 'Write': return '#ea580c' 
    case 'Full': return '#dc2626'
    default: return '#64748b'
  }
}

// Watch for modal open/close
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen && props.recordId) {
    await Promise.all([fetchRecordAccess(), fetchUsers(), fetchGroups()])
  }
  if (!isOpen) {
    error.value = null
    showGrantForm.value = false
  }
})

const closeModal = () => {
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="modal-overlay" @click="closeModal">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <h3>Manage Access: {{ recordType }} #{{ recordId }}</h3>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>
      
      <div class="modal-body">
        <p v-if="error" class="error-message">{{ error }}</p>
        
        <!-- Grant New Access Section -->
        <div class="grant-section">
          <div class="section-header">
            <h4>Grant Access</h4>
            <button 
              v-if="!showGrantForm"
              @click="showGrantForm = true"
              class="btn-primary btn-small"
            >
              Add Permission
            </button>
          </div>
          
          <form v-if="showGrantForm" @submit.prevent="grantAccess" class="grant-form">
            <div class="form-row">
              <div class="form-group">
                <label>Grant To</label>
                <div class="grant-options">
                  <label class="radio-label">
                    <input 
                      type="radio" 
                      value="user" 
                      :checked="newAccess.user_id !== null"
                      @change="newAccess.group_id = null"
                    />
                    User
                  </label>
                  <label class="radio-label">
                    <input 
                      type="radio" 
                      value="group" 
                      :checked="newAccess.group_id !== null"
                      @change="newAccess.user_id = null"
                    />
                    Group
                  </label>
                </div>
              </div>
              
              <div class="form-group">
                <label>Access Level</label>
                <select v-model="newAccess.access_level" class="form-input" required>
                  <option value="Read">Read</option>
                  <option value="Write">Write</option>
                  <option value="Full">Full</option>
                </select>
              </div>
            </div>
            
            <div class="form-row">
              <div v-if="newAccess.user_id !== null" class="form-group">
                <label>User</label>
                <select v-model="newAccess.user_id" class="form-input" required>
                  <option value="">Choose user...</option>
                  <option v-for="user in users" :key="user.id" :value="user.id">
                    {{ user.full_name }} (@{{ user.username }})
                  </option>
                </select>
              </div>
              
              <div v-if="newAccess.group_id !== null" class="form-group">
                <label>Group</label>
                <select v-model="newAccess.group_id" class="form-input" required>
                  <option value="">Choose group...</option>
                  <option v-for="group in groups" :key="group.id" :value="group.id">
                    {{ group.name }}
                  </option>
                </select>
              </div>
              
              <div class="form-group">
                <label>Expires At (Optional)</label>
                <input 
                  v-model="newAccess.expires_at" 
                  type="datetime-local" 
                  class="form-input"
                />
              </div>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="showGrantForm = false" class="btn-secondary">
                Cancel
              </button>
              <button type="submit" class="btn-primary">
                Grant Access
              </button>
            </div>
          </form>
        </div>
        
        <!-- Current Access List -->
        <div class="access-list-section">
          <h4>Current Permissions ({{ accesses.length }})</h4>
          
          <div v-if="loading">Loading permissions...</div>
          
          <div v-else-if="accesses.length === 0" class="empty-state">
            No specific permissions granted. Access is controlled by user roles.
          </div>
          
          <div v-else class="access-list">
            <div v-for="access in accesses" :key="access.id" class="access-item">
              <div class="access-info">
                <div class="access-target">
                  <span v-if="access.user_id" class="target-user">
                    👤 {{ getUserById(access.user_id)?.full_name || 'Unknown User' }}
                    <small>@{{ getUserById(access.user_id)?.username }}</small>
                  </span>
                  <span v-else-if="access.group_id" class="target-group">
                    👥 {{ getGroupById(access.group_id)?.name || 'Unknown Group' }}
                  </span>
                </div>
                
                <div class="access-details">
                  <span 
                    class="access-badge" 
                    :style="{ backgroundColor: getAccessLevelColor(access.access_level), color: 'white' }"
                  >
                    {{ access.access_level }}
                  </span>
                  
                  <span v-if="access.expires_at" class="expires-info">
                    Expires: {{ new Date(access.expires_at).toLocaleDateString() }}
                  </span>
                  
                  <span class="granted-info">
                    Granted {{ new Date(access.granted_at || '').toLocaleDateString() }}
                  </span>
                </div>
              </div>
              
              <button 
                @click="revokeAccess(access.id)"
                class="btn-danger btn-small"
              >
                Revoke
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 700px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-muted);
}

.modal-body {
  padding: 1.5rem;
}

.grant-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h4 {
  margin: 0;
}

.btn-small {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

.grant-form {
  background-color: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.grant-options {
  display: flex;
  gap: 1rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.form-input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.1);
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.btn-secondary {
  background-color: #f1f5f9;
  color: #475569;
  border: 1px solid #cbd5e1;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-danger {
  background-color: #dc2626;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.access-list-section h4 {
  margin-bottom: 1rem;
}

.access-list {
  space-y: 0.75rem;
}

.access-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 0.75rem;
}

.access-target {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.target-user small, .target-group small {
  font-weight: normal;
  color: var(--color-muted);
  display: block;
  margin-top: 0.25rem;
}

.access-details {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.access-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.expires-info, .granted-info {
  font-size: 0.8rem;
  color: var(--color-muted);
}

.empty-state {
  text-align: center;
  color: var(--color-muted);
  padding: 2rem;
  font-style: italic;
}

.error-message {
  color: #dc2626;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .access-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .modal {
    margin: 1rem;
    max-width: none;
  }
}
</style>
