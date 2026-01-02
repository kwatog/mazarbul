<script setup lang="ts">
import { type Component, h } from 'vue'
import { InboxIcon } from '@heroicons/vue/24/outline'

withDefaults(defineProps<{
  title: string
  description?: string
  actionText?: string
  icon?: Component
}>(), {
  description: '',
  icon: InboxIcon
})

const emit = defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="empty-state">
    <div class="empty-state-icon">
      <slot name="icon">
        <component :is="icon" class="empty-state-svg" />
      </slot>
    </div>
    
    <h3 class="empty-state-title">{{ title }}</h3>
    
    <p v-if="description" class="empty-state-description">{{ description }}</p>
    
    <div v-if="actionText || $slots.actions" class="empty-state-actions">
      <slot name="actions">
        <button class="empty-state-btn" @click="emit('action')">
          {{ actionText }}
        </button>
      </slot>
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12) var(--spacing-6);
  text-align: center;
}

.empty-state-icon {
  margin-bottom: var(--spacing-4);
}

.empty-state-svg {
  width: 64px;
  height: 64px;
  color: var(--color-gray-300);
}

.empty-state-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-gray-900);
  margin: 0 0 var(--spacing-2);
}

.empty-state-description {
  font-size: var(--text-base);
  color: var(--color-gray-500);
  margin: 0 0 var(--spacing-6);
  max-width: 400px;
}

.empty-state-actions {
  margin-top: var(--spacing-2);
}

.empty-state-btn {
  background: var(--color-primary);
  color: white;
  border: none;
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.empty-state-btn:hover {
  background: #17c653;
}
</style>
