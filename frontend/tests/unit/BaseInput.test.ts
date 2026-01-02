import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import BaseInput from '../../components/base/BaseInput.vue'
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline'

describe('BaseInput', () => {
  it('renders input element', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '' }
    })
    expect(wrapper.find('input').exists()).toBe(true)
  })

  it('binds modelValue', async () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: 'test value' }
    })
    expect(wrapper.find('input').element.value).toBe('test value')
  })

  it('updates modelValue on input', async () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '' }
    })
    await wrapper.find('input').setValue('new value')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['new value'])
  })

  it('displays label when provided', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', label: 'Username' }
    })
    expect(wrapper.find('label').text()).toBe('Username')
  })

  it('shows required indicator when required', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', required: true, label: 'Username' }
    })
    // Required indicator is shown as span with asterisk
    expect(wrapper.html()).toContain('*')
  })

  it('displays error message', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', error: 'This field is required' }
    })
    expect(wrapper.find('.base-input-error').text()).toBe('This field is required')
  })

  it('displays help text', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', helpText: 'Enter your username' }
    })
    expect(wrapper.find('.base-input-help').text()).toBe('Enter your username')
  })

  it('shows error state styling', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', error: 'Error' }
    })
    expect(wrapper.find('.base-input-container').classes()).toContain('base-input-container--error')
  })

  it('is disabled when disabled prop is set', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', disabled: true }
    })
    expect(wrapper.find('input').attributes('disabled')).toBeDefined()
    expect(wrapper.find('.base-input-container').classes()).toContain('base-input-container--disabled')
  })

  it('applies focus class when focused', async () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '' }
    })
    await wrapper.find('input').trigger('focus')
    expect(wrapper.find('.base-input-container').classes()).toContain('base-input-container--focused')
  })

  it('renders prefix icon when provided', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', prefixIcon: MagnifyingGlassIcon }
    })
    expect(wrapper.findComponent(MagnifyingGlassIcon).exists()).toBe(true)
    expect(wrapper.find('.base-input-prefix-icon').exists()).toBe(true)
  })

  it('renders suffix icon when provided', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', suffixIcon: MagnifyingGlassIcon }
    })
    expect(wrapper.findComponent(MagnifyingGlassIcon).exists()).toBe(true)
    expect(wrapper.find('.base-input-suffix-icon').exists()).toBe(true)
  })

  it('accepts different input types', () => {
    const types = ['text', 'email', 'number', 'password', 'date', 'search', 'tel', 'url'] as const
    
    types.forEach(type => {
      const wrapper = mount(BaseInput, {
        props: { modelValue: '', type }
      })
      expect(wrapper.find('input').attributes('type')).toBe(type)
    })
  })

  it('generates unique id when not provided', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '' }
    })
    expect(wrapper.find('input').attributes('id')).toBeDefined()
  })

  it('uses provided id', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', id: 'my-input', label: 'My Input' }
    })
    expect(wrapper.find('input').attributes('id')).toBe('my-input')
    expect(wrapper.find('label').attributes('for')).toBe('my-input')
  })

  it('sets placeholder', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', placeholder: 'Enter value...' }
    })
    expect(wrapper.find('input').attributes('placeholder')).toBe('Enter value...')
  })

  it('sets maxlength', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', maxlength: 50 }
    })
    expect(wrapper.find('input').attributes('maxlength')).toBe('50')
  })

  it('emits focus event', async () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '' }
    })
    await wrapper.find('input').trigger('focus')
    expect(wrapper.emitted('focus')).toBeTruthy()
  })

  it('emits blur event', async () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '' }
    })
    await wrapper.find('input').trigger('blur')
    expect(wrapper.emitted('blur')).toBeTruthy()
  })
})
