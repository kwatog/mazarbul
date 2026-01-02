<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { 
  HomeIcon, 
  CurrencyDollarIcon, 
  BriefcaseIcon, 
  FolderIcon,
  UserGroupIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowLeftOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  ChevronDownIcon
} from '@heroicons/vue/24/outline'

const userCookie = useCookie('user_info')
const tokenCookie = useCookie('access_token')

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

const user = ref(decodeUserInfo(userCookie.value))
const mobileMenuOpen = ref(false)

watch(userCookie, (newVal) => {
  user.value = decodeUserInfo(newVal)
})

const logout = async () => {
  tokenCookie.value = null
  userCookie.value = null
  user.value = null
  await navigateTo('/login')
}

const isAdminOrManager = computed(() => {
  return user.value && ['Admin', 'Manager'].includes(user.value.role)
})

const isActive = (path: string) => {
  if (path === '/') {
    return useRoute().path === '/'
  }
  return useRoute().path.startsWith(path)
}

const closeMobileMenu = () => {
  mobileMenuOpen.value = false
}
</script>

<template>
  <div>
    <header class="header" v-if="$route.path !== '/login'">
      <div class="header-left">
        <NuxtLink to="/" class="logo" @click="closeMobileMenu">
          <div class="logo-icon">
            <ChartBarIcon class="logo-svg" />
          </div>
          <div class="logo-text">
            <span class="logo-title">Ebrose</span>
            <span class="logo-sub">Chamber of Spend Records</span>
          </div>
        </NuxtLink>
      </div>

      <!-- Mobile Hamburger -->
      <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="Toggle menu">
        <Bars3Icon v-if="!mobileMenuOpen" class="menu-icon" />
        <XMarkIcon v-else class="menu-icon" />
      </button>

      <nav class="nav-main" :class="{ 'nav-mobile-open': mobileMenuOpen }">
        <div class="nav-section">
          <NuxtLink to="/" class="nav-link" :class="{ active: isActive('/') && $route.path === '/' }" @click="closeMobileMenu">
            <HomeIcon class="nav-icon-svg" aria-hidden="true" />
            <span class="nav-label">Dashboard</span>
          </NuxtLink>

          <div class="nav-dropdown">
            <button class="nav-link nav-dropdown-trigger">
              <CurrencyDollarIcon class="nav-icon-svg" aria-hidden="true" />
              <span class="nav-label">Finance</span>
              <ChevronDownIcon class="nav-arrow-svg" aria-hidden="true" />
            </button>
            <div class="nav-dropdown-menu">
              <NuxtLink to="/budget-items" class="nav-dropdown-item" @click="closeMobileMenu">Budget Items</NuxtLink>
              <NuxtLink to="/business-cases" class="nav-dropdown-item" @click="closeMobileMenu">Business Cases</NuxtLink>
              <NuxtLink to="/line-items" class="nav-dropdown-item" @click="closeMobileMenu">Line Items</NuxtLink>
            </div>
          </div>

          <div class="nav-dropdown">
            <button class="nav-link nav-dropdown-trigger">
              <FolderIcon class="nav-icon-svg" aria-hidden="true" />
              <span class="nav-label">Projects</span>
              <ChevronDownIcon class="nav-arrow-svg" aria-hidden="true" />
            </button>
            <div class="nav-dropdown-menu">
              <NuxtLink to="/wbs" class="nav-dropdown-item" @click="closeMobileMenu">WBS</NuxtLink>
              <NuxtLink to="/assets" class="nav-dropdown-item" @click="closeMobileMenu">Assets</NuxtLink>
              <NuxtLink to="/purchase-orders" class="nav-dropdown-item" @click="closeMobileMenu">Purchase Orders</NuxtLink>
              <NuxtLink to="/goods-receipts" class="nav-dropdown-item" @click="closeMobileMenu">Goods Receipts</NuxtLink>
            </div>
          </div>

          <NuxtLink to="/resources" class="nav-link" :class="{ active: isActive('/resources') }" @click="closeMobileMenu">
            <UserGroupIcon class="nav-icon-svg" aria-hidden="true" />
            <span class="nav-label">Resources</span>
          </NuxtLink>

          <NuxtLink to="/allocations" class="nav-link" :class="{ active: isActive('/allocations') }" @click="closeMobileMenu">
            <BriefcaseIcon class="nav-icon-svg" aria-hidden="true" />
            <span class="nav-label">Allocations</span>
          </NuxtLink>
        </div>

        <div class="nav-section nav-section-right">
          <template v-if="isAdminOrManager">
            <div class="nav-dropdown">
              <button class="nav-link nav-dropdown-trigger admin-trigger">
                <Cog6ToothIcon class="nav-icon-svg" aria-hidden="true" />
                <span class="nav-label">Admin</span>
                <ChevronDownIcon class="nav-arrow-svg" aria-hidden="true" />
              </button>
              <div class="nav-dropdown-menu nav-dropdown-right">
                <NuxtLink to="/admin/groups" class="nav-dropdown-item" @click="closeMobileMenu">User Groups</NuxtLink>
                <NuxtLink to="/admin/audit" class="nav-dropdown-item" @click="closeMobileMenu">Audit Logs</NuxtLink>
              </div>
            </div>
          </template>

          <div class="user-section">
            <div class="user-avatar">{{ user?.username?.charAt(0)?.toUpperCase() || '?' }}</div>
            <div class="user-info">
              <span class="user-name">{{ user?.username }}</span>
              <span class="user-role">{{ user?.role }}</span>
            </div>
            <button @click="logout" class="logout-btn" title="Logout" aria-label="Logout">
              <ArrowLeftOnRectangleIcon class="logout-icon" aria-hidden="true" />
            </button>
          </div>
        </div>
      </nav>
    </header>
    <main class="main-container">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.header {
  background: white;
  border-bottom: 1px solid var(--color-gray-200);
  padding: 0 var(--spacing-6);
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  box-shadow: var(--shadow-sm);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  text-decoration: none;
  color: inherit;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-svg {
  width: 24px;
  height: 24px;
  color: white;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-gray-900);
  line-height: 1.2;
}

.logo-sub {
  font-size: var(--text-xs);
  color: var(--color-gray-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Mobile Menu Button */
.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  padding: var(--spacing-2);
  cursor: pointer;
  color: var(--color-gray-700);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.menu-icon {
  width: 24px;
  height: 24px;
}

.mobile-menu-btn:hover {
  background: var(--color-gray-100);
  color: var(--color-gray-900);
}

.nav-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  margin-left: var(--spacing-8);
  height: 100%;
}

.nav-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  height: 100%;
}

.nav-section-right {
  gap: var(--spacing-2);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: var(--color-gray-600);
  font-size: var(--text-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
  border: none;
  background: none;
  cursor: pointer;
}

.nav-link:hover {
  background: var(--color-gray-100);
  color: var(--color-gray-900);
}

.nav-link.active {
  background: #eff6ff;
  color: #2563eb;
}

.nav-icon-svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  display: none;
}

.nav-arrow-svg {
  width: 16px;
  height: 16px;
  margin-left: var(--spacing-1);
  opacity: 0.6;
  transition: transform var(--transition-fast);
}

.nav-dropdown {
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
}

.nav-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.nav-dropdown:hover .nav-arrow-svg {
  transform: rotate(180deg);
}

.nav-dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 200px;
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: var(--spacing-2);
  opacity: 0;
  visibility: hidden;
  transform: translateY(10px);
  transition: all var(--transition-base);
  margin-top: var(--spacing-2);
  border: 1px solid var(--color-gray-100);
}

.nav-dropdown:hover .nav-dropdown-menu,
.nav-dropdown-trigger:focus + .nav-dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.nav-dropdown-right {
  left: auto;
  right: 0;
}

.nav-dropdown-item {
  display: block;
  padding: var(--spacing-3) var(--spacing-4);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: var(--color-gray-600);
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
}

.nav-dropdown-item:hover {
  background: var(--color-gray-100);
  color: var(--color-gray-900);
}

.user-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding-left: var(--spacing-4);
  border-left: 1px solid var(--color-gray-200);
  margin-left: var(--spacing-2);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--text-sm);
}

.user-info {
  display: none;
  flex-direction: column;
}

.user-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-gray-900);
}

.user-role {
  font-size: var(--text-xs);
  color: var(--color-gray-500);
}

.logout-btn {
  background: none;
  border: none;
  padding: var(--spacing-2);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-gray-500);
}

.logout-icon {
  width: 20px;
  height: 20px;
}

.logout-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

/* Desktop: Show labels */
@media (min-width: 768px) {
  .nav-label {
    display: inline;
  }

  .nav-link {
    padding: var(--spacing-2) var(--spacing-4);
  }

  .user-info {
    display: flex;
  }
}

/* Mobile Styles */
@media (max-width: 767px) {
  .header {
    padding: 0 var(--spacing-4);
  }

  .logo-sub {
    display: none;
  }

  .mobile-menu-btn {
    display: block;
  }

  .nav-main {
    position: fixed;
    top: 64px;
    left: 0;
    right: 0;
    bottom: 0;
    background: white;
    flex-direction: column;
    align-items: stretch;
    justify-content: flex-start;
    margin-left: 0;
    padding: var(--spacing-4);
    overflow-y: auto;
    transform: translateX(-100%);
    transition: transform var(--transition-base);
    z-index: var(--z-modal);
    box-shadow: var(--shadow-lg);
  }

  .nav-main.nav-mobile-open {
    transform: translateX(0);
  }

  .nav-section {
    flex-direction: column;
    align-items: stretch;
    height: auto;
    gap: var(--spacing-2);
  }

  .nav-section-right {
    gap: var(--spacing-2);
    margin-top: var(--spacing-6);
    padding-top: var(--spacing-6);
    border-top: 1px solid var(--color-gray-200);
  }

  .nav-link {
    padding: var(--spacing-3) var(--spacing-4);
    justify-content: flex-start;
  }

  .nav-label {
    display: inline;
  }

  .nav-dropdown {
    height: auto;
  }

  .nav-dropdown-menu {
    position: static;
    opacity: 1;
    visibility: visible;
    transform: none;
    margin-top: var(--spacing-1);
    margin-left: var(--spacing-6);
    box-shadow: none;
    border: none;
    background: var(--color-gray-50);
  }

  .user-info {
    display: flex;
  }

  .user-section {
    padding-left: 0;
    border-left: none;
    margin-left: 0;
    justify-content: space-between;
    padding: var(--spacing-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
  }
}
</style>
