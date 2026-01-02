import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import BaseButton from '../../components/base/BaseButton.vue'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'

describe('BaseButton', () => {
  it('renders button element', () => {
    const wrapper = mount(BaseButton, {
      slots: { default: 'Click me' }
    })
    expect(wrapper.find('button').exists()).toBe(true)
    expect(wrapper.text()).toBe('Click me')
  })

  it('applies variant classes', () => {
    const variants = ['primary', 'secondary', 'ghost', 'danger', 'success'] as const
    
    variants.forEach(variant => {
      const wrapper = mount(BaseButton, {
        props: { variant },
        slots: { default: 'Test' }
      })
      expect(wrapper.find('button').classes()).toContain(`base-button--${variant}`)
    })
  })

  it('applies size classes', () => {
    const sizes = ['xs', 'sm', 'md', 'lg'] as const
    
    sizes.forEach(size => {
      const wrapper = mount(BaseButton, {
        props: { size },
        slots: { default: 'Test' }
      })
      expect(wrapper.find('button').classes()).toContain(`base-button--${size}`)
    })
  })

  it('shows loading spinner when loading', () => {
    const wrapper = mount(BaseButton, {
      props: { loading: true }
    })
    expect(wrapper.findComponent(ArrowPathIcon).exists()).toBe(true)
    expect(wrapper.find('button').classes()).toContain('base-button--loading')
  })

  it('is disabled when loading', () => {
    const wrapper = mount(BaseButton, {
      props: { loading: true }
    })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('is disabled when disabled prop is set', () => {
    const wrapper = mount(BaseButton, {
      props: { disabled: true }
    })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    expect(wrapper.find('button').classes()).toContain('base-button--disabled')
  })

  it('emits click event', async () => {
    const wrapper = mount(BaseButton, {
      slots: { default: 'Click me' }
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })

  it('does not emit click when disabled', async () => {
    const wrapper = mount(BaseButton, {
      props: { disabled: true }
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('does not emit click when loading', async () => {
    const wrapper = mount(BaseButton, {
      props: { loading: true }
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('renders icon when provided', () => {
    const wrapper = mount(BaseButton, {
      props: { icon: ArrowPathIcon }
    })
    expect(wrapper.findComponent(ArrowPathIcon).exists()).toBe(true)
  })

  it('applies full-width class when fullWidth is true', () => {
    const wrapper = mount(BaseButton, {
      props: { fullWidth: true }
    })
    expect(wrapper.find('button').classes()).toContain('base-button--full-width')
  })

  it('handles iconRight prop', () => {
    const wrapper = mount(BaseButton, {
      props: { icon: ArrowPathIcon, iconRight: true },
      slots: { default: 'With Icon' }
    })
    expect(wrapper.find('button').html()).toContain('button-icon')
  })

  it('has correct type attribute', () => {
    const types = ['button', 'submit', 'reset'] as const
    
    types.forEach(type => {
      const wrapper = mount(BaseButton, {
        props: { type },
        slots: { default: 'Test' }
      })
      expect(wrapper.find('button').attributes('type')).toBe(type)
    })
  })
})
