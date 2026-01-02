import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import BaseTable from '../../components/base/BaseTable.vue'

describe('BaseTable', () => {
  const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'role', label: 'Role' }
  ]

  const data = [
    { name: 'John Doe', email: 'john@example.com', role: 'Admin' },
    { name: 'Jane Smith', email: 'jane@example.com', role: 'User' },
    { name: 'Bob Wilson', email: 'bob@example.com', role: 'Manager' }
  ]

  it('renders table element', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data }
    })
    expect(wrapper.find('table.base-table').exists()).toBe(true)
  })

  it('renders table headers', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data }
    })
    const headers = wrapper.findAll('.base-table-header')
    expect(headers).toHaveLength(3)
    expect(headers[0].text()).toBe('Name')
    expect(headers[1].text()).toBe('Email')
    expect(headers[2].text()).toBe('Role')
  })

  it('renders table rows', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data }
    })
    const rows = wrapper.findAll('.base-table-row')
    expect(rows).toHaveLength(3)
  })

  it('renders cell content', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data }
    })
    const cells = wrapper.findAll('.base-table-cell')
    expect(cells[0].text()).toBe('John Doe')
    expect(cells[1].text()).toBe('john@example.com')
  })

  it('shows empty message when no data', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data: [], emptyMessage: 'No records found' }
    })
    expect(wrapper.find('.base-table-empty').text()).toBe('No records found')
  })

  it('shows loading skeleton', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data, loading: true }
    })
    expect(wrapper.findAll('.base-table-row.loading')).toHaveLength(5)
  })

  it('sorts data when sortable column clicked', async () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data }
    })
    await wrapper.findAll('.base-table-header')[0].trigger('click')
    expect(wrapper.emitted('sort')).toBeTruthy()
  })

  it('shows sort indicator for sorted column', async () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data }
    })
    await wrapper.findAll('.base-table-header')[0].trigger('click')
    expect(wrapper.find('.sort-icon').exists()).toBe(true)
  })

  it('emits row-click event', async () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data }
    })
    await wrapper.findAll('.base-table-row')[0].trigger('click')
    expect(wrapper.emitted('row-click')).toBeTruthy()
    expect(wrapper.emitted('row-click')?.[0]).toEqual([data[0]])
  })

  it('renders custom cell slots', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data },
      slots: {
        'cell-name': '<strong>{{ value }}</strong>'
      }
    })
    expect(wrapper.find('.base-table-cell strong').exists()).toBe(true)
  })

  it('applies align classes', () => {
    const alignedColumns = [
      { key: 'left', label: 'Left', align: 'left' as const },
      { key: 'center', label: 'Center', align: 'center' as const },
      { key: 'right', label: 'Right', align: 'right' as const }
    ]
    const wrapper = mount(BaseTable, {
      props: { columns: alignedColumns, data: [{ left: 'a', center: 'b', right: 'c' }] }
    })
    expect(wrapper.findAll('.base-table-cell')[0].classes()).toContain('text-left')
    expect(wrapper.findAll('.base-table-cell')[1].classes()).toContain('text-center')
    expect(wrapper.findAll('.base-table-cell')[2].classes()).toContain('text-right')
  })

  it('shows checkbox column when selectable', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data, selectable: true }
    })
    expect(wrapper.find('.base-table-checkbox').exists()).toBe(true)
    expect(wrapper.findAll('.base-table-checkbox')).toHaveLength(4) // 3 rows + header
  })

  it('selects all when header checkbox clicked', async () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data, selectable: true }
    })
    await wrapper.find('.base-table-checkbox input').trigger('change')
    expect(wrapper.emitted('selection-change')).toBeTruthy()
  })

  it('emits sort event with key and direction', async () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data }
    })
    await wrapper.findAll('.base-table-header')[0].trigger('click')
    expect(wrapper.emitted('sort')?.[0]).toEqual(['name', 'asc'])
    
    await wrapper.findAll('.base-table-header')[0].trigger('click')
    expect(wrapper.emitted('sort')?.[1]).toEqual(['name', 'desc'])
  })

  it('applies sticky header class', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data, stickyHeader: true }
    })
    expect(wrapper.find('.base-table-container').classes()).toContain('sticky-header')
  })

  it('renders pagination slot', () => {
    const wrapper = mount(BaseTable, {
      props: { columns, data },
      slots: {
        pagination: '<div class="pagination">Page 1</div>'
      }
    })
    expect(wrapper.find('.base-table-pagination').exists()).toBe(true)
    expect(wrapper.find('.pagination').exists()).toBe(true)
  })

  it('sets column width', () => {
    const columnsWithWidth = [
      { key: 'name', label: 'Name', width: '200px' },
      { key: 'email', label: 'Email' }
    ]
    const wrapper = mount(BaseTable, {
      props: { columns: columnsWithWidth, data }
    })
    const headers = wrapper.findAll('.base-table-header')
    expect(headers[0].attributes('style')).toContain('200px')
  })
})
