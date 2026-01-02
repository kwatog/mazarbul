<script setup lang="ts">
import { ref, computed, useId } from 'vue'
import { ChevronUpDownIcon, CheckIcon } from '@heroicons/vue/24/outline'

interface Option {
  value: string | number
  label: string
  disabled?: boolean
}

const uid = useId()

const props = withDefaults(defineProps<{
  modelValue: string | number | null | undefined
  options: Option[]
  label?: string
  placeholder?: string
  error?: string
  disabled?: boolean
  required?: boolean
  multiple?: boolean
  searchable?: boolean
  size?: 'sm' | 'md' | 'lg'
}>(), {
  placeholder: 'Select an option',
  disabled: false,
  required: false,
  multiple: false,
  searchable: false,
  size: 'md'
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
  'change': [value: any]
  'focus': []
  'blur': []
}>()

const searchQuery = ref('')
const isOpen = ref(false)
const selectedIndex = ref(-1)

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  return props.options.filter(opt => 
    opt.label.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const selectedLabel = computed(() => {
  const selected = props.options.find(opt => opt.value === props.modelValue)
  return selected?.label || props.placeholder
})

const isSelected = (value: string | number) => {
  if (props.multiple) {
    const arr = props.modelValue as any[]
    return arr?.includes(value)
  }
  return props.modelValue === value
}

const selectOption = (option: Option) => {
  if (option.disabled) return

  if (props.multiple) {
    const current = (props.modelValue as any[]) || []
    const index = current.indexOf(option.value)
    if (index === -1) {
      emit('update:modelValue', [...current, option.value])
    } else {
      emit('update:modelValue', current.filter(v => v !== option.value))
    }
  } else {
    emit('update:modelValue', option.value)
    isOpen.value = false
  }
  emit('change', props.modelValue)
}

const onFocus = () => {
  isOpen.value = true
  emit('focus')
}

const onBlur = () => {
  emit('blur')
  setTimeout(() => {
    isOpen.value = false
  }, 200)
}

const sizeClasses = {
  sm: 'base-select-sm',
  md: 'base-select-md',
  lg: 'base-select-lg'
}
</script>

<template>
  <div class="base-select-wrapper">
    <label v-if="label" :id="'base-select-label-' + uid" class="base-select-label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    
    <div 
      class="base-select" 
      :class="[sizeClasses[size], { 'is-open': isOpen, 'is-error': error, 'is-disabled': disabled }]"
      role="combobox"
      :aria-expanded="isOpen"
      :aria-disabled="disabled"
      :aria-labelledby="label ? 'base-select-label-' + uid : undefined"
      :aria-controls="'base-select-dropdown-' + uid"
    >
      <div 
        class="base-select-trigger" 
        @click="!disabled && (isOpen = !isOpen)"
        :id="'base-select-trigger-' + uid"
        role="combobox"
        :aria-expanded="isOpen"
        :aria-controls="'base-select-dropdown-' + uid"
        tabindex="0"
      >
        <input
          v-if="searchable"
          v-model="searchQuery"
          type="text"
          class="base-select-search"
          :placeholder="typeof modelValue === 'undefined' || modelValue === null ? placeholder : ''"
          @focus="onFocus"
          @blur="onBlur"
        />
        <span v-else class="base-select-value">{{ selectedLabel }}</span>
        <ChevronUpDownIcon class="base-select-arrow" aria-hidden="true" />
      </div>

      <Transition name="dropdown">
        <div 
          v-if="isOpen" 
          :id="'base-select-dropdown-' + uid" 
          class="base-select-dropdown"
          role="listbox"
        >
          <div
            v-for="(option, index) in filteredOptions"
            :key="option.value"
            class="base-select-option"
            :class="{ 
              'is-selected': isSelected(option.value),
              'is-disabled': option.disabled,
              'is-highlighted': index === selectedIndex
            }"
            role="option"
            :aria-selected="isSelected(option.value)"
            :aria-disabled="option.disabled"
            @click="selectOption(option)"
          >
            <CheckIcon v-if="isSelected(option.value)" class="base-select-option-check" aria-hidden="true" />
            {{ option.label }}
          </div>
          <div v-if="filteredOptions.length === 0" class="base-select-empty">
            No results found
          </div>
        </div>
      </Transition>
    </div>

    <p v-if="error" class="base-select-error">{{ error }}</p>
    <p v-else-if="$slots.help" class="base-select-help">
      <slot name="help" />
    </p>
  </div>
</template>

<style scoped>
.base-select-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.base-select-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-gray-700);
}

.required {
  color: var(--color-error);
}

.base-select {
  position: relative;
  width: 100%;
  background: white;
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.base-select:hover {
  border-color: var(--color-gray-400);
}

.base-select:focus-within,
.base-select.is-open {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.1);
}

.base-select.is-error {
  border-color: var(--color-error);
}

.base-select.is-error:focus-within {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.base-select.is-disabled {
  background: var(--color-gray-100);
  cursor: not-allowed;
  opacity: 0.7;
}

.base-select-sm {
  min-height: 32px;
  font-size: var(--text-sm);
}

.base-select-md {
  min-height: 40px;
  font-size: var(--text-base);
}

.base-select-lg {
  min-height: 48px;
  font-size: var(--text-lg);
}

.base-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-2) var(--spacing-3);
  height: 100%;
}

.base-select-value {
  flex: 1;
  color: var(--color-gray-900);
}

.base-select-search {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: inherit;
}

.base-select-arrow {
  width: 1.25rem;
  height: 1.25rem;
  color: var(--color-gray-500);
  transition: transform var(--transition-fast);
  flex-shrink: 0;
}

.base-select.is-open .base-select-arrow {
  transform: rotate(180deg);
}

.base-select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: var(--spacing-1);
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-height: 240px;
  overflow-y: auto;
  z-index: var(--z-dropdown);
}

.base-select-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.base-select-option:hover,
.base-select-option.is-highlighted {
  background: var(--color-gray-100);
}

.base-select-option.is-selected {
  color: var(--color-primary);
  font-weight: 500;
}

.base-select-option.is-disabled {
  color: var(--color-gray-400);
  cursor: not-allowed;
}

.base-select-option-check {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.base-select-empty {
  padding: var(--spacing-3);
  text-align: center;
  color: var(--color-gray-500);
  font-size: var(--text-sm);
}

.base-select-error {
  font-size: var(--text-sm);
  color: var(--color-error);
}

.base-select-help {
  font-size: var(--text-sm);
  color: var(--color-gray-500);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
