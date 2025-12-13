<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.apiBase || config.public.apiBase
const token = useCookie('access_token')
const userInfo = useCookie('user_info')

// Parse user info to check role
const currentUser = userInfo.value ? JSON.parse(userInfo.value as string) : null

// Redirect if not Manager or Admin
if (!currentUser || !['Manager', 'Admin'].includes(currentUser.role)) {
  await navigateTo('/')
}

interface UserGroup {
  id: number
  name: string
  description: string
  created_by?: number
  created_at?: string
}

interface User {
  id: number
  username: string
  full_name: string
  department: string
  role: string
}

interface GroupMembership {
  id: number
  user_id: number
  group_id: number
  added_by?: number
  added_at?: string
}

const groups = ref<UserGroup[]>([])
const users = ref<User[]>([])
const selectedGroup = ref<UserGroup | null>(null)
const groupMembers = ref<GroupMembership[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Form states
const showCreateGroupModal = ref(false)
const showAddMemberModal = ref(false)
const newGroup = ref({
  name: '',
  description: ''
})
const selectedUserId = ref<number | null>(null)

const fetchGroups = async () => {
  try {
    const res = await useApiFetch<UserGroup[]>(`/user-groups`)
    groups.value = res
  } catch (e: any) {
    error.value = 'Failed to load groups'
    if (e.response?.status === 401) await navigateTo('/login')
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

const fetchGroupMembers = async (groupId: number) => {
  try {
    const res = await useApiFetch<GroupMembership[]>(`/user-groups/${groupId}/members`)
    groupMembers.value = res
  } catch (e: any) {
    error.value = 'Failed to load group members'
  }
}

const createGroup = async () => {
  try {
    await useApiFetch(`/user-groups`, { method: 'POST', body: newGroup.value })
    
    newGroup.value = { name: '', description: '' }
    showCreateGroupModal.value = false
    await fetchGroups()
  } catch (e: any) {
    error.value = e.data?.detail || 'Failed to create group'
  }
}

const addMemberToGroup = async () => {
  if (!selectedGroup.value || !selectedUserId.value) return
  
  try {
    await useApiFetch(`/user-groups/${selectedGroup.value.id}/members`, {
      method: 'POST',
      body: {
        user_id: selectedUserId.value,
        group_id: selectedGroup.value.id
      }
    })
    
    selectedUserId.value = null
    showAddMemberModal.value = false
    await fetchGroupMembers(selectedGroup.value.id)
  } catch (e: any) {
    error.value = e.data?.detail || 'Failed to add member'
  }
}

const removeMemberFromGroup = async (userId: number) => {
  if (!selectedGroup.value) return
  
  try {
    await useApiFetch(`/user-groups/${selectedGroup.value.id}/members/${userId}`, { method: 'DELETE' })
    
    await fetchGroupMembers(selectedGroup.value.id)
  } catch (e: any) {
    error.value = e.data?.detail || 'Failed to remove member'
  }
}

const selectGroup = async (group: UserGroup) => {
  selectedGroup.value = group
  await fetchGroupMembers(group.id)
}

const getUserById = (userId: number) => {
  return users.value.find(u => u.id === userId)
}

onMounted(async () => {
  await Promise.all([fetchGroups(), fetchUsers()])
  loading.value = false
})
</script>

<template>
  <div>
    <div class="admin-header">
      <h1 class="page-title">User Groups Management</h1>
      <p class="page-subtitle">Manage user groups and memberships</p>
      
      <button 
        @click="showCreateGroupModal = true" 
        class="btn-primary"
        style="margin-top: 1rem;"
      >
        Create New Group
      </button>
    </div>

    <p v-if="loading">Loading groups...</p>
    <p v-else-if="error" style="color: #dc2626;">{{ error }}</p>
    
    <div v-else class="groups-layout">
      <!-- Groups List -->
      <div class="groups-panel card">
        <h2 class="card-title">Groups ({{ groups.length }})</h2>
        
        <div v-if="groups.length === 0" class="empty-state">
          No groups found. Create your first group!
        </div>
        
        <div v-else class="groups-list">
          <div 
            v-for="group in groups" 
            :key="group.id"
            class="group-item"
            :class="{ active: selectedGroup?.id === group.id }"
            @click="selectGroup(group)"
          >
            <div class="group-name">{{ group.name }}</div>
            <div class="group-desc">{{ group.description || 'No description' }}</div>
          </div>
        </div>
      </div>

      <!-- Group Members -->
      <div v-if="selectedGroup" class="members-panel card">
        <div class="panel-header">
          <h2 class="card-title">{{ selectedGroup.name }} Members</h2>
          <button 
            @click="showAddMemberModal = true" 
            class="btn-primary btn-small"
          >
            Add Member
          </button>
        </div>
        
        <div v-if="groupMembers.length === 0" class="empty-state">
          No members in this group.
        </div>
        
        <div v-else class="members-list">
          <div 
            v-for="membership in groupMembers" 
            :key="membership.id"
            class="member-item"
          >
            <div class="member-info">
              <div class="member-name">
                {{ getUserById(membership.user_id)?.full_name || 'Unknown User' }}
              </div>
              <div class="member-details">
                @{{ getUserById(membership.user_id)?.username }} • 
                {{ getUserById(membership.user_id)?.role }}
              </div>
            </div>
            <button 
              @click="removeMemberFromGroup(membership.user_id)"
              class="btn-danger btn-small"
            >
              Remove
            </button>
          </div>
        </div>
      </div>
      
      <!-- Placeholder when no group selected -->
      <div v-else class="placeholder-panel card">
        <div class="placeholder-content">
          <h3>Select a Group</h3>
          <p>Choose a group from the left to view and manage its members.</p>
        </div>
      </div>
    </div>

    <!-- Create Group Modal -->
    <div v-if="showCreateGroupModal" class="modal-overlay" @click="showCreateGroupModal = false">
      <div class="modal" @click.stop>
        <h3>Create New Group</h3>
        
        <form @submit.prevent="createGroup">
          <div class="form-group">
            <label for="groupName">Group Name</label>
            <input 
              id="groupName"
              v-model="newGroup.name" 
              type="text" 
              required 
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="groupDesc">Description</label>
            <textarea 
              id="groupDesc"
              v-model="newGroup.description" 
              class="form-input"
              rows="3"
            ></textarea>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="showCreateGroupModal = false" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary">
              Create Group
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add Member Modal -->
    <div v-if="showAddMemberModal" class="modal-overlay" @click="showAddMemberModal = false">
      <div class="modal" @click.stop>
        <h3>Add Member to {{ selectedGroup?.name }}</h3>
        
        <form @submit.prevent="addMemberToGroup">
          <div class="form-group">
            <label for="userSelect">Select User</label>
            <select 
              id="userSelect"
              v-model="selectedUserId" 
              required 
              class="form-input"
            >
              <option value="">Choose a user...</option>
              <option 
                v-for="user in users.filter(u => !groupMembers.some(m => m.user_id === u.id))" 
                :key="user.id"
                :value="user.id"
              >
                {{ user.full_name }} (@{{ user.username }}) - {{ user.role }}
              </option>
            </select>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="showAddMemberModal = false" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary">
              Add Member
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-header {
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  color: var(--color-muted);
  font-size: 1.1rem;
  margin-bottom: 0;
}

.groups-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  min-height: 500px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.groups-list, .members-list {
  space-y: 0.75rem;
}

.group-item, .member-item {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 0.75rem;
}

.group-item:hover {
  border-color: var(--color-primary);
  background-color: rgba(30, 215, 96, 0.05);
}

.group-item.active {
  border-color: var(--color-primary);
  background-color: rgba(30, 215, 96, 0.1);
}

.group-name, .member-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.group-desc, .member-details {
  font-size: 0.9rem;
  color: var(--color-muted);
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: default;
}

.member-item:hover {
  border-color: #cbd5e1;
}

.placeholder-panel {
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-content {
  text-align: center;
  color: var(--color-muted);
}

.empty-state {
  text-align: center;
  color: var(--color-muted);
  padding: 2rem;
  font-style: italic;
}

.btn-small {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

.btn-secondary {
  background-color: #f1f5f9;
  color: #475569;
  border: 1px solid #cbd5e1;
  padding: 0.6rem 1.3rem;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 600;
}

.btn-danger {
  background-color: #dc2626;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

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
  padding: 2rem;
  width: 100%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.1);
}

textarea.form-input {
  resize: vertical;
  min-height: 80px;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

@media (max-width: 900px) {
  .groups-layout {
    grid-template-columns: 1fr;
  }
  
  .modal {
    margin: 1rem;
    max-width: none;
  }
}
</style>
