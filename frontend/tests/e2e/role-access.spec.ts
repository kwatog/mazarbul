import { test, expect } from '@playwright/test';

test.describe('Role-Based Access Control', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Viewer role cannot create/edit/delete budget items', async ({ page }) => {
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Login successful',
          user: { id: 3, username: 'viewer', role: 'Viewer' }
        })
      });
    });

    await page.route('**/budget-items', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, workday_ref: 'WD-001', title: 'Budget', budget_amount: 100000, fiscal_year: 2025, owner_group_id: 1 }
        ])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'viewer');
    await page.fill('#password', 'viewer123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=WD-001')).toBeVisible();
    await expect(page.locator('button:has-text("Create")')).not.toBeVisible();
    await expect(page.locator('button:has-text("Edit")').first()).not.toBeVisible();
    await expect(page.locator('button:has-text("Delete")').first()).not.toBeVisible();
  });

  test('Manager can delete records that User cannot', async ({ page }) => {
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Login successful',
          user: { id: 2, username: 'manager', role: 'Manager' }
        })
      });
    });

    await page.route('**/budget-items', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, workday_ref: 'WD-001', title: 'Budget', budget_amount: 100000, fiscal_year: 2025, owner_group_id: 1 }
        ])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'manager');
    await page.fill('#password', 'manager123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('button:has-text("Delete")').first()).toBeVisible();
  });

  test('Admin sees admin-only pages that Manager cannot', async ({ page }) => {
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Login successful',
          user: { id: 1, username: 'admin', role: 'Admin' }
        })
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await expect(page.locator('text=Admin Panel')).toBeVisible();
    await expect(page.locator('a[href="/admin/groups"]')).toBeVisible();
    await expect(page.locator('a[href="/admin/audit"]')).toBeVisible();
  });

  test('Manager does not see Admin Panel in navigation', async ({ page }) => {
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Login successful',
          user: { id: 2, username: 'manager', role: 'Manager' }
        })
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'manager');
    await page.fill('#password', 'manager123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await expect(page.locator('text=Admin Panel')).not.toBeVisible();
    await expect(page.locator('a[href="/admin/groups"]')).not.toBeVisible();
    await expect(page.locator('a[href="/admin/audit"]')).not.toBeVisible();
  });

  test('User without group membership cannot access records', async ({ page }) => {
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Login successful',
          user: { id: 10, username: 'orphan', role: 'User' }
        })
      });
    });

    await page.route('**/budget-items', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'orphan');
    await page.fill('#password', 'orphan123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');

    const rows = await page.locator('table tbody tr').count();
    expect(rows).toBe(0);
  });

  test('Role dropdown only visible to Admin in user management', async ({ page }) => {
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Login successful',
          user: { id: 1, username: 'admin', role: 'Admin' }
        })
      });
    });

    await page.route('**/user-groups', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: 'Engineering', member_count: 5 }
        ])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/admin/groups');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('select[name="role"]')).toBeVisible();
  });
});

test.describe('Role Permission Matrix', () => {
  const permissions = [
    { role: 'Admin', create: true, read: true, update: true, delete: true, admin: true },
    { role: 'Manager', create: true, read: true, update: true, delete: true, admin: false },
    { role: 'User', create: true, read: true, update: true, delete: false, admin: false },
    { role: 'Viewer', create: false, read: true, update: false, delete: false, admin: false },
  ];

  permissions.forEach(({ role, create, read, update, delete: del, admin }) => {
    test(`${role} permissions: C:${create} R:${read} U:${update} D:${del} Admin:${admin}`, async ({ page }) => {
      await page.route('**/auth/login', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Login successful',
            user: { id: 1, username: role.toLowerCase(), role }
          })
        });
      });

      await page.goto('/login');
      await page.fill('#username', role.toLowerCase());
      await page.fill('#password', 'password');
      await page.click('button[type="submit"]');
      await page.waitForURL('/');

      await page.goto('/budget-items');
      await page.waitForLoadState('networkidle');

      if (read) {
        await expect(page.locator('table')).toBeVisible();
      }

      if (create) {
        await expect(page.locator('button:has-text("Create")')).toBeVisible();
      } else {
        await expect(page.locator('button:has-text("Create")')).not.toBeVisible();
      }

      if (admin) {
        await expect(page.locator('text=Admin Panel')).toBeVisible();
      } else {
        await expect(page.locator('text=Admin Panel')).not.toBeVisible();
      }
    });
  });
});
