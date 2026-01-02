# Frontend Pages

Base URL (local): `http://localhost:3000`

---

## UI Component Library

All pages use a consistent set of base UI components defined in `frontend/components/base/`:

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **BaseButton** | Primary interactive element | 5 variants, 4 sizes, loading state, Heroicons |
| **BaseInput** | Text input fields | Validation, Heroicons, error states |
| **BaseSelect** | Dropdown selection | Searchable, multi-select, ARIA accessible, ChevronUpDownIcon |
| **BaseTextarea** | Multi-line input | Auto-resize, character count |
| **BaseModal** | Dialog overlay | Focus trap, scroll lock, animations, XMarkIcon close |
| **BaseTable** | Data display | Sorting, selection, sticky header, ArrowUp/ArrowDown icons |
| **BaseBadge** | Status indicators | 6 color variants, sizes |
| **BaseCard** | Content container | Header/footer slots, padding options |
| **BaseDropdown** | Menu dropdown | Hover/click triggers, keyboard nav |
| **LoadingSpinner** | Loading indicator | 5 sizes, 3 colors, ArrowPathIcon |
| **EmptyState** | Empty data placeholder | InboxIcon, description, action |

### Heroicons Integration

All components use [Heroicons](https://heroicons.com/) for consistent iconography:

| Icon | Component | Usage |
|------|-----------|-------|
| `ArrowPathIcon` | BaseButton | Loading spinner |
| `ArrowUpIcon` / `ArrowDownIcon` | BaseTable | Sort indicators |
| `ChevronUpDownIcon` | BaseSelect | Dropdown arrow |
| `CheckIcon` | BaseSelect | Selection checkmark |
| `XMarkIcon` | BaseModal | Close button |
| `InboxIcon` | EmptyState | Default empty state icon |

### Composables

| Composable | Purpose |
|------------|---------|
| **useToast** | Toast notifications (success/error/info) |
| **useApiFetch** | API wrapper with auto cookies & 401 refresh |

### Mobile Responsive Navigation

The layout includes a responsive hamburger menu with Heroicons:
- `Bars3Icon` - Menu toggle (closed)
- `XMarkIcon` - Menu toggle (open)
- Navigation icons: HomeIcon, CurrencyDollarIcon, FolderIcon, UserGroupIcon, BriefcaseIcon, Cog6ToothIcon, ArrowLeftOnRectangleIcon

---

## Public Pages

| Route | Description |
|-------|-------------|
| `/login` | Login page with username/password |
| `/health` | Frontend health status page |
| `/component-test` | Test page for all UI components |

---

## Main Application Pages

### Dashboard (`/`)
- System health indicator
- Navigation to all entity pages
- Quick stats summary

### Budget Items (`/budget-items`)
- List all accessible budgets
- Create/Edit/Delete budgets
- Filter by fiscal year
- Share budget with users/groups

**Columns:**
- Workday Ref
- Title
- Budget Amount (2dp formatting)
- Fiscal Year
- Owner Group
- Created By
- Actions (Edit, Share, Delete)

---

### Business Cases (`/business-cases`)
- List business cases (hybrid access)
- Create new business case
- Status workflow: Draft → Submitted → Review → Approved/Rejected
- Add line items
- View linked budgets

---

### Line Items (`/line-items`)
- List line items (budget-to-BC linking)
- Create line item
- Select budget item and business case
- Set spend category (CAPEX/OPEX)
- Set requested amount

---

### WBS (`/wbs`)
- Work Breakdown Structure items
- Create WBS linked to line item
- Inherits owner_group_id from parent

---

### Assets (`/assets`)
- Fixed assets tracking
- Create asset linked to WBS
- Inherits owner_group_id from WBS
- Asset codes and types

---

### Purchase Orders (`/purchase-orders`)
- PO management
- Create PO linked to asset
- Inherits owner_group_id from asset
- Status tracking (Open, Issued, Closed)

---

### Goods Receipts (`/goods-receipts`)
- Receipt tracking
- Create GR linked to PO
- Inherits owner_group_id from PO
- Amount and date tracking

---

### Resources (`/resources`)
- Vendor resource management
- Create resource with monthly cost
- Cost per month with 2dp formatting

---

### Allocations (`/allocations`)
- Resource-to-PO allocations
- Create allocation linked to resource and PO
- Expected monthly burn rate

---

## Admin Pages

### User Groups (`/admin/groups`)
**Requires:** Admin or Manager role

- List all user groups
- Create/Edit/Delete groups
- Add/Remove group members
- View member list

---

### Audit Logs (`/admin/audit`)
**Requires:** Admin role only

- View complete audit trail
- Filter by user
- Filter by date range
- Expand to see old/new values (JSON diff)
- Export audit data

---

## Authentication Flow

1. User navigates to `/login`
2. Enters credentials
3. Backend sets HttpOnly cookies
4. User redirected to `/`
5. Middleware checks `user_info` cookie
6. Access granted/denied based on role

---

## Navigation Structure

```
┌─────────────────────────────────────────┐
│  Logo    │  Budgets  BCs  LineItems... │  [User Menu]
├─────────────────────────────────────────┤
│                                         │
│           Page Content                  │
│                                         │
└─────────────────────────────────────────┘
```

### Admin Dropdown (Admin/Manager only)
- User Groups
- Audit Logs

---

## Record Sharing Modal

Accessed from any record detail page via "Share" button.

**Features:**
- Grant access to specific user
- Grant access to group
- Set access level (Read/Write/Full)
- Set expiration date
- View existing grants
- Revoke access

---

## Shared Components

### RecordAccessModal.vue
- Grant/revoke record access
- User/group selection
- Access level dropdown
- Expiration date picker

### ToastNotification.vue
- Global toast notification system
- Success/error/info variants
- Auto-dismiss after 4 seconds
- Click to dismiss

### useApiFetch.ts
- Wrapper around fetch with automatic cookies
- Refresh-on-401 behavior
- Consistent error handling

### auth.global.ts
- Global route guard
- Checks user_info cookie
- Redirects to /login if not authenticated

### useToast.ts
```typescript
const { success, error, info, toasts } = useToast()

// Show success message
success('Record saved successfully!')

// Show error message  
error('Failed to save record')

// Show info message
info('Processing your request...')
```

---

## Design System

### CSS Variables

All components use CSS variables from `frontend/assets/css/main.css`:

```css
/* Colors */
--color-primary, --color-success, --color-error
--color-gray-100 through --color-gray-900

/* Spacing */
--spacing-1 through --spacing-16

/* Typography */
--text-xs through --text-4xl

/* Border Radius */
--radius-sm, --radius-md, --radius-lg, --radius-xl

/* Transitions */
--transition-fast, --transition-base, --transition-slow
```

### Component Test Page

Visit `/component-test` to verify all base components render correctly with:
- All button variants and sizes
- Input states (focus, error, disabled)
- Modal sizes and animations
- Loading spinner sizes and colors
- Interactive form submission

---

## Role-Based UI

| Role | Admin Panel | Delete Records | See All Records |
|------|-------------|----------------|-----------------|
| Admin | ✅ | ✅ | ✅ |
| Manager | ✅ (Groups only) | ✅ | ✅ |
| User | ❌ | ❌ | Own + Group + Shared |
| Viewer | ❌ | ❌ | Read only |

---

## Currency Formatting

All monetary values displayed with:
- 2 decimal places
- Locale-formatted numbers (1,000,000.00)
- Currency symbol (USD by default)

---

## Loading States

- Skeleton loaders on data fetching
- Button spinners during form submission
- Toast notifications for success/error

---

## Form Validation

- Required field validation
- Numeric range validation
- Date format validation
- Duplicate reference checking

---

## Screenshot Gallery

Updated screenshots captured January 2026 with Heroicons UI:

| Screenshot | Description |
|------------|-------------|
| `screenshots/01-login-page.png` | Login page |
| `screenshots/02-dashboard.png` | Dashboard with health check |
| `screenshots/03-budget-items-list.png` | Budget items list with filters |
| `screenshots/04-budget-items-create-modal.png` | Create budget item modal |
| `screenshots/05-purchase-orders.png` | Purchase orders management |
| `screenshots/05b-purchase-orders-create-modal.png` | Create PO modal with all fields |
| `screenshots/06-wbs.png` | Work Breakdown Structure page |
| `screenshots/06b-wbs-create-modal.png` | Create WBS modal |
| `screenshots/07-assets.png` | Assets tracking page |
| `screenshots/07b-assets-create-modal.png` | Create asset modal |
| `screenshots/08-admin-groups.png` | User groups management |
| `screenshots/09-admin-audit.png` | Audit log viewer |
| `screenshots/10-business-cases.png` | Business cases page |
| `screenshots/11-goods-receipts.png` | Goods receipts tracking |
| `screenshots/11b-goods-receipts-create-modal.png` | Create GR modal |

All screenshots are located in `frontend/screenshots/` and reflect the updated base component library with Heroicons.
