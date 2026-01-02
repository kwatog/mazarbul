/**
 * Icon mapping composable
 * Maps semantic icon names to Heroicons components
 */

import {
  HomeIcon,
  CurrencyDollarIcon,
  FolderIcon,
  UsersIcon,
  ChartBarIcon,
  CogIcon,
  ArrowRightOnRectangleIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  BriefcaseIcon,
  CubeIcon,
  ShoppingCartIcon,
  InboxIcon,
  UserGroupIcon,
  ClipboardDocumentCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

import {
  CheckCircleIcon as CheckCircleIconSolid,
  XCircleIcon as XCircleIconSolid,
  ExclamationTriangleIcon as ExclamationTriangleIconSolid,
  InformationCircleIcon as InformationCircleIconSolid,
} from '@heroicons/vue/24/solid'

export type IconName =
  // Navigation
  | 'home'
  | 'finance'
  | 'projects'
  | 'resources'
  | 'allocations'
  | 'admin'
  | 'logout'
  // Actions
  | 'plus'
  | 'edit'
  | 'delete'
  | 'search'
  | 'filter'
  // Entities
  | 'budget-item'
  | 'business-case'
  | 'line-item'
  | 'wbs'
  | 'asset'
  | 'purchase-order'
  | 'goods-receipt'
  | 'user-group'
  | 'allocation'
  // Status
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  // UI
  | 'chevron-down'
  | 'chevron-up'
  | 'menu'
  | 'close'

export const useIcons = () => {
  const icons = {
    // Navigation
    home: HomeIcon,
    finance: CurrencyDollarIcon,
    projects: FolderIcon,
    resources: UsersIcon,
    allocations: ChartBarIcon,
    admin: CogIcon,
    logout: ArrowRightOnRectangleIcon,

    // Actions
    plus: PlusIcon,
    edit: PencilIcon,
    delete: TrashIcon,
    search: MagnifyingGlassIcon,
    filter: FunnelIcon,

    // Entities
    'budget-item': DocumentTextIcon,
    'business-case': BriefcaseIcon,
    'line-item': ClipboardDocumentListIcon,
    wbs: FolderIcon,
    asset: CubeIcon,
    'purchase-order': ShoppingCartIcon,
    'goods-receipt': InboxIcon,
    'user-group': UserGroupIcon,
    allocation: ClipboardDocumentCheckIcon,

    // Status (outline)
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,

    // UI
    'chevron-down': ChevronDownIcon,
    'chevron-up': ChevronUpIcon,
    menu: Bars3Icon,
    close: XMarkIcon,
  }

  const solidIcons = {
    success: CheckCircleIconSolid,
    error: XCircleIconSolid,
    warning: ExclamationTriangleIconSolid,
    info: InformationCircleIconSolid,
  }

  /**
   * Get an icon component by name
   * @param name - The semantic icon name
   * @param solid - Whether to use solid variant (only available for status icons)
   */
  const getIcon = (name: IconName, solid = false) => {
    if (solid && name in solidIcons) {
      return solidIcons[name as keyof typeof solidIcons]
    }
    return icons[name]
  }

  return {
    icons,
    solidIcons,
    getIcon,
  }
}
