<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/vue/24/solid'

interface Column {
  key: string
  label: string
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
}

const props = withDefaults(defineProps<{
  columns: Column[]
  data: Record<string, any>[]
  loading?: boolean
  selectable?: boolean
  stickyHeader?: boolean
  emptyMessage?: string
}>(), {
  loading: false,
  selectable: false,
  stickyHeader: false,
  emptyMessage: 'No data available'
})

const emit = defineEmits<{
  'row-click': [row: Record<string, any>]
  'selection-change': [selected: Record<string, any>[]]
  'sort': [key: string, direction: 'asc' | 'desc']
}>()

const sortKey = ref('')
const sortDirection = ref<'asc' | 'desc'>('asc')
const selectedRows = ref<Set<number>>(new Set())

const sortedData = computed(() => {
  if (!sortKey.value) return props.data
  return [...props.data].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]
    const modifier = sortDirection.value === 'asc' ? 1 : -1
    if (aVal < bVal) return -1 * modifier
    if (aVal > bVal) return 1 * modifier
    return 0
  })
})

const toggleSort = (key: string) => {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
  emit('sort', sortKey.value, sortDirection.value)
}

const toggleSelectAll = () => {
  if (selectedRows.value.size === sortedData.value.length) {
    selectedRows.value.clear()
  } else {
    sortedData.value.forEach((_, index) => selectedRows.value.add(index))
  }
  emit('selection-change', sortedData.value.filter((_, i) => selectedRows.value.has(i)))
}

const toggleRow = (index: number) => {
  if (selectedRows.value.has(index)) {
    selectedRows.value.delete(index)
  } else {
    selectedRows.value.add(index)
  }
  emit('selection-change', sortedData.value.filter((_, i) => selectedRows.value.has(i)))
}

const alignClass = (align?: string) => {
  return align ? `text-${align}` : 'text-left'
}
</script>

<template>
  <div class="base-table-wrapper">
    <div class="base-table-container" :class="{ 'sticky-header': stickyHeader }">
      <table class="base-table">
        <thead>
          <tr>
            <th v-if="selectable" class="base-table-checkbox">
              <input 
                type="checkbox" 
                :checked="selectedRows.size === data.length && data.length > 0"
                :indeterminate="selectedRows.size > 0 && selectedRows.size < data.length"
                @change="toggleSelectAll"
              />
            </th>
            <th 
              v-for="col in columns" 
              :key="col.key"
              :style="{ width: col.width }"
              :class="['base-table-header', alignClass(col.align), { sortable: col.sortable }]"
              @click="col.sortable && toggleSort(col.key)"
            >
              {{ col.label }}
              <span v-if="col.sortable && sortKey === col.key" class="sort-indicator">
                <ArrowUpIcon v-if="sortDirection === 'asc'" class="sort-icon" aria-hidden="true" />
                <ArrowDownIcon v-else class="sort-icon" aria-hidden="true" />
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 5" :key="n" class="base-table-row loading">
              <td v-if="selectable"><div class="skeleton-checkbox"></div></td>
              <td v-for="col in columns" :key="col.key">
                <div class="skeleton-line"></div>
              </td>
            </tr>
          </template>
          
          <template v-else-if="data.length === 0">
            <tr>
              <td :colspan="columns.length + (selectable ? 1 : 0)" class="base-table-empty">
                {{ emptyMessage }}
              </td>
            </tr>
          </template>
          
          <template v-else>
            <tr 
              v-for="(row, index) in sortedData" 
              :key="index"
              class="base-table-row"
              :class="{ 'is-selected': selectedRows.has(index) }"
              @click="emit('row-click', row)"
            >
              <td v-if="selectable" class="base-table-checkbox">
                <input 
                  type="checkbox" 
                  :checked="selectedRows.has(index)"
                  @change="toggleRow(index)"
                  @click.stop
                />
              </td>
              <td 
                v-for="col in columns" 
                :key="col.key"
                :class="['base-table-cell', alignClass(col.align)]"
              >
                <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                  {{ row[col.key] }}
                </slot>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    
    <div v-if="$slots.pagination" class="base-table-pagination">
      <slot name="pagination" />
    </div>
  </div>
</template>

<style scoped>
.base-table-wrapper {
  width: 100%;
}

.base-table-container {
  overflow-x: auto;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-gray-200);
}

.base-table-container.sticky-header thead {
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;
}

.base-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.base-table-header {
  padding: var(--spacing-3) var(--spacing-4);
  text-align: left;
  font-weight: 600;
  color: var(--color-gray-700);
  background: var(--color-gray-50);
  border-bottom: 2px solid var(--color-gray-200);
  white-space: nowrap;
}

.base-table-header.sortable {
  cursor: pointer;
  user-select: none;
}

.base-table-header.sortable:hover {
  background: var(--color-gray-100);
}

.sort-indicator {
  margin-left: var(--spacing-1);
  display: inline-flex;
  align-items: center;
}

.sort-icon {
  width: 1rem;
  height: 1rem;
  color: var(--color-primary);
}

.base-table-cell {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-gray-100);
  color: var(--color-gray-900);
}

.base-table-row {
  transition: background var(--transition-fast);
}

.base-table-row:hover:not(.loading) {
  background: var(--color-gray-50);
}

.base-table-row.is-selected {
  background: #eff6ff;
}

.base-table-row.loading .skeleton-line,
.base-table-row.loading .skeleton-checkbox {
  background: linear-gradient(90deg, var(--color-gray-200) 25%, var(--color-gray-100) 50%, var(--color-gray-200) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton-line {
  height: 16px;
  width: 80%;
}

.skeleton-checkbox {
  width: 18px;
  height: 18px;
}

.base-table-checkbox {
  width: 48px;
  text-align: center;
}

.base-table-checkbox input {
  cursor: pointer;
}

.base-table-empty {
  padding: var(--spacing-12) var(--spacing-6);
  text-align: center;
  color: var(--color-gray-500);
}

.base-table-pagination {
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-gray-200);
}

.text-left {
  text-align: left;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
