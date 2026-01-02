import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import EmptyState from '../../components/base/EmptyState.vue'
import { InboxIcon, PlusIcon } from '@heroicons/vue/24/outline'

describe('EmptyState', () => {
  it('renders title', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'No items found' }
    })
    expect(wrapper.find('.empty-state-title').text()).toBe('No items found')
  })

  it('renders description when provided', () => {
    const wrapper = mount(EmptyState, {
      props: { 
        title: 'No items',
        description: 'Get started by creating your first item.'
      }
    })
    expect(wrapper.find('.empty-state-description').text()).toBe('Get started by creating your first item.')
  })

  it('does not render description when empty', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'No items' }
    })
    expect(wrapper.find('.empty-state-description').exists()).toBe(false)
  })

  it('renders default icon', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'No items' }
    })
    // Icon is rendered as a component slot
    expect(wrapper.find('.empty-state-svg').exists()).toBe(true)
  })

  it('renders custom icon when provided', () => {
    const wrapper = mount(EmptyState, {
      props: { 
        title: 'No items',
        icon: PlusIcon
      }
    })
    // Custom icon replaces the default
    expect(wrapper.find('.empty-state-svg').exists()).toBe(true)
  })

  it('renders icon slot', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'No items' },
      slots: {
        icon: '<svg class="custom-icon" data-testid="custom-icon"></svg>'
      }
    })
    expect(wrapper.find('.custom-icon').exists()).toBe(true)
  })

  it('renders action button when actionText is provided', () => {
    const wrapper = mount(EmptyState, {
      props: { 
        title: 'No items',
        actionText: 'Create Item'
      }
    })
    expect(wrapper.find('.empty-state-btn').exists()).toBe(true)
    expect(wrapper.find('.empty-state-btn').text()).toBe('Create Item')
  })

  it('emits action event when button clicked', async () => {
    const wrapper = mount(EmptyState, {
      props: { 
        title: 'No items',
        actionText: 'Create Item'
      }
    })
    await wrapper.find('.empty-state-btn').trigger('click')
    expect(wrapper.emitted('action')).toBeTruthy()
  })

  it('renders actions slot', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'No items' },
      slots: {
        actions: '<button class="custom-btn">Custom Action</button>'
      }
    })
    expect(wrapper.find('.custom-btn').exists()).toBe(true)
  })

  it('does not render action section when no actionText or actions slot', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'No items' }
    })
    expect(wrapper.find('.empty-state-actions').exists()).toBe(false)
  })

  it('centers content properly', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'Test' }
    })
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.find('.empty-state-title').exists()).toBe(true)
    expect(wrapper.find('.empty-state-icon').exists()).toBe(true)
  })
})
