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

const showCreateGroupModal = ref(false)
const showEditGroupModal = ref(false)
const showAddMemberModal = ref(false)
const showMembersModal = ref(false)

const form = ref({
  name: '',
  description: ''
})

const selectedUserId = ref<number | null>(null)

const userOptions = computed(() => {
  const memberUserIds = groupMembers.value.map(m => m.user_id)
  return users.value
    .filter(u => !memberUserIds.includes(u.id))
    .map(u => ({
      value: u.id,
      label: `${u.full_name} (@${u.username}) - ${u.role}`
    }))
})

const fetchGroups = async () => {
  try {
    loading.value = true
    const res = await useApiFetch<UserGroup[]>('/user-groups')
    groups.value = res as any
    error.value = null
  } catch (e: any) {
    error.value = 'Failed to load groups'
    if (e.response?.status === 401) {
      await navigateTo('/login')
    }
  } finally {
    loading.value = false
  }
}

const fetchUsers = async () => {
  try {
    const res = await useApiFetch<User[]>('/users')
    users.value = res as any
  } catch (e: any) {
    console.error('Failed to load users:', e)
  }
}

const fetchGroupMembers = async (groupId: number) => {
  try {
    const res = await useApiFetch<GroupMembership[]>(`/user-groups/${groupId}/members`)
    groupMembers.value = res as any
  } catch (e: any) {
    showError('Failed to load group members')
  }
}

const resetForm = () => {
  form.value = {
    name: '',
    description: ''
  }
}

const openCreateModal = () => {
  resetForm()
  showCreateGroupModal.value = true
}

const openEditModal = (group: UserGroup) => {
  selectedGroup.value = group
  form.value = {
    name: group.name,
    description: group.description || ''
  }
  showEditGroupModal.value = true
}

const openMembersModal = async (group: UserGroup) => {
  selectedGroup.value = group
  await fetchGroupMembers(group.id)
  showMembersModal.value = true
}

const closeModals = () => {
  showCreateGroupModal.value = false
  showEditGroupModal.value = false
  showMembersModal.value = false
  showAddMemberModal.value = false
  selectedGroup.value = null
  resetForm()
}

const createGroup = async () => {
  try {
    loading.value = true
    await useApiFetch('/user-groups', {
      method: 'POST',
      body: form.value
    })
    await fetchGroups()
    closeModals()
    success('Group created successfully!')
  } catch (e: any) {
    showError(e.data?.detail || 'Failed to create group')
  } finally {
    loading.value = false
  }
}

const updateGroup = async () => {
  if (!selectedGroup.value) return
  try {
    loading.value = true
    await useApiFetch(`/user-groups/${selectedGroup.value.id}`, {
      method: 'PUT',
      body: form.value
    })
    await fetchGroups()
    closeModals()
    success('Group updated successfully!')
  } catch (e: any) {
    showError(e.data?.detail || 'Failed to update group')
  } finally {
    loading.value = false
  }
}

const deleteGroup = async (group: UserGroup) => {
  if (!confirm(`Are you sure you want to delete group "${group.name}"?`)) {
    return
  }
  try {
    loading.value = true
    await useApiFetch(`/user-groups/${group.id}`, { method: 'DELETE' })
    await fetchGroups()
    success('Group deleted successfully!')
  } catch (e: any) {
    showError(e.data?.detail || 'Failed to delete group')
  } finally {
    loading.value = false
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
    success('Member added successfully!')
  } catch (e: any) {
    showError(e.data?.detail || 'Failed to add member')
  }
}

const removeMemberFromGroup = async (userId: number) => {
  if (!selectedGroup.value) return
  const user = getUserById(userId)
  if (!confirm(`Are you sure you want to remove ${user?.full_name} from this group?`)) {
    return
  }
  try {
    await useApiFetch(`/user-groups/${selectedGroup.value.id}/members/${userId}`, {
      method: 'DELETE'
    })
    await fetchGroupMembers(selectedGroup.value.id)
    success('Member removed successfully!')
  } catch (e: any) {
    showError(e.data?.detail || 'Failed to remove member')
  }
}

const getUserById = (userId: number) => {
  return users.value.find(u => u.id === userId)
}

const getMemberCount = (groupId: number) => {
  // This would ideally come from the API, but for now we'll return a placeholder
  return 0
}

const tableColumns = [
  { key: 'name', label: 'Group Name', sortable: true },
  { key: 'description', label: 'Description', sortable: false },
  { key: 'created_at', label: 'Created', sortable: true },
  { key: 'actions', label: 'Actions', sortable: false }
]

const formatDate = (dateStr?: string) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

onMounted(async () => {
  await Promise.all([fetchGroups(), fetchUsers()])
})
</script>

<template>
  <BaseCard title="User Groups" subtitle="Manage user groups and memberships">
    <template #header>
      <div class="header-actions">
        <BaseButton variant="primary" @click="openCreateModal">
          + Create Group
        </BaseButton>
      </div>
    </template>

    <div v-if="loading" class="loading-state" role="status" aria-live="polite">
      <LoadingSpinner size="lg" label="Loading groups..." />
    </div>

    <p v-else-if="error" class="error-message" role="alert">{{ error }}</p>

    <EmptyState
      v-else-if="groups.length === 0"
      title="No groups found"
      description="Create your first group to organize users and manage permissions."
      action-text="Create Group"
      @action="openCreateModal"
    />

    <BaseTable
      v-else
      :columns="tableColumns"
      :data="groups"
      :loading="loading"
      selectable
      sticky-header
      empty-message="No groups found"
    >
      <template #cell-name="{ value, row }">
        <div>
          <strong>{{ value }}</strong>
        </div>
      </template>

      <template #cell-description="{ value }">
        <span class="description">{{ value || 'No description' }}</span>
      </template>

      <template #cell-created_at="{ value }">
        <span class="date-text">{{ formatDate(value) }}</span>
      </template>

      <template #cell-actions="{ row }">
        <div class="action-buttons">
          <BaseButton
            size="sm"
            variant="secondary"
            @click.stop="openMembersModal(row)"
          >
            Members
          </BaseButton>
          <BaseButton
            size="sm"
            variant="secondary"
            @click.stop="openEditModal(row)"
          >
            Edit
          </BaseButton>
          <BaseButton
            size="sm"
            variant="danger"
            @click.stop="deleteGroup(row)"
          >
            Delete
          </BaseButton>
        </div>
      </template>
    </BaseTable>

    <!-- Create Group Modal -->
    <BaseModal
      v-model="showCreateGroupModal"
      title="Create New Group"
      size="md"
      @close="closeModals"
    >
      <form @submit.prevent="createGroup">
        <BaseInput
          v-model="form.name"
          label="Group Name"
          placeholder="e.g., Engineering Team"
          required
        />

        <BaseTextarea
          v-model="form.description"
          label="Description"
          placeholder="Optional description of the group's purpose"
          rows="3"
        />
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="createGroup">
          Create Group
        </BaseButton>
      </template>
    </BaseModal>

    <!-- Edit Group Modal -->
    <BaseModal
      v-model="showEditGroupModal"
      title="Edit Group"
      size="md"
      @close="closeModals"
    >
      <form @submit.prevent="updateGroup">
        <BaseInput
          v-model="form.name"
          label="Group Name"
          required
        />

        <BaseTextarea
          v-model="form.description"
          label="Description"
          placeholder="Optional description of the group's purpose"
          rows="3"
        />
      </form>

      <template #footer>
        <BaseButton variant="secondary" :disabled="loading" @click="closeModals">
          Cancel
        </BaseButton>
        <BaseButton variant="primary" :loading="loading" @click="updateGroup">
          Save Changes
        </BaseButton>
      </template>
    </BaseModal>

    <!-- Members Management Modal -->
    <BaseModal
      v-model="showMembersModal"
      :title="`${selectedGroup?.name} - Members`"
      size="lg"
      @close="closeModals"
    >
      <div class="members-section">
        <div class="members-header">
          <h3 class="members-title">Group Members</h3>
          <BaseButton
            size="sm"
            variant="primary"
            @click="showAddMemberModal = true"
          >
            + Add Member
          </BaseButton>
        </div>

        <EmptyState
          v-if="groupMembers.length === 0"
          title="No members"
          description="Add members to this group to grant them collective permissions."
        />

        <div v-else class="members-list" role="list">
          <div
            v-for="membership in groupMembers"
            :key="membership.id"
            class="member-item"
            role="listitem"
          >
            <div class="member-info">
              <div class="member-name">
                {{ getUserById(membership.user_id)?.full_name || 'Unknown User' }}
              </div>
              <div class="member-details">
                @{{ getUserById(membership.user_id)?.username }} -
                {{ getUserById(membership.user_id)?.role }}
                <span v-if="getUserById(membership.user_id)?.department" class="member-department">
                  | {{ getUserById(membership.user_id)?.department }}
                </span>
              </div>
            </div>
            <BaseButton
              size="sm"
              variant="danger"
              @click="removeMemberFromGroup(membership.user_id)"
            >
              Remove
            </BaseButton>
          </div>
        </div>
      </div>

      <template #footer>
        <BaseButton variant="secondary" @click="closeModals">
          Close
        </BaseButton>
      </template>
    </BaseModal>

    <!-- Add Member Modal -->
    <BaseModal
      v-model="showAddMemberModal"
      :title="`Add Member to ${selectedGroup?.name}`"
      size="md"
      @close="showAddMemberModal = false"
    >
      <form @submit.prevent="addMemberToGroup">
        <BaseSelect
          v-model="selectedUserId"
          :options="userOptions"
          label="Select User"
          placeholder="Choose a user to add..."
          required
        />
      </form>

      <template #footer>
        <BaseButton variant="secondary" @click="showAddMemberModal = false">
          Cancel
        </BaseButton>
        <BaseButton
          variant="primary"
          :disabled="!selectedUserId"
          @click="addMemberToGroup"
        >
          Add Member
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

.description {
  font-size: var(--text-sm);
  color: var(--color-gray-500);
}

.date-text {
  font-size: var(--text-sm);
  color: var(--color-gray-600);
}

.action-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.members-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.members-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--color-gray-200);
}

.members-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-gray-900);
  margin: 0;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  max-height: 400px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.member-item:hover {
  border-color: var(--color-gray-300);
  background-color: var(--color-gray-50);
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.member-name {
  font-weight: 600;
  color: var(--color-gray-900);
}

.member-details {
  font-size: var(--text-sm);
  color: var(--color-gray-500);
}

.member-department {
  color: var(--color-gray-400);
}

@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
  }

  .members-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-3);
  }

  .member-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-3);
  }
}
</style>
