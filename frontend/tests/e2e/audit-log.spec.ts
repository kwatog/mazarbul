import { test, expect } from '@playwright/test';

test.describe('Audit Log Viewer', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Admin can view complete audit trail', async ({ page }) => {
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

    await page.route('**/audit-logs', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            table_name: 'budget_item',
            record_id: 1,
            action: 'CREATE',
            user_id: 1,
            username: 'admin',
            new_values: { title: 'Test Budget', budget_amount: 100000 },
            timestamp: new Date().toISOString()
          },
          {
            id: 2,
            table_name: 'budget_item',
            record_id: 1,
            action: 'UPDATE',
            user_id: 1,
            username: 'admin',
            old_values: { title: 'Test Budget' },
            new_values: { title: 'Updated Budget' },
            timestamp: new Date().toISOString()
          },
          {
            id: 3,
            table_name: 'purchase_order',
            record_id: 1,
            action: 'DELETE',
            user_id: 2,
            username: 'manager',
            old_values: { po_number: 'PO-001' },
            timestamp: new Date().toISOString()
          }
        ])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/admin/audit');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Audit Logs')).toBeVisible();
    await expect(page.locator('text=CREATE')).toBeVisible();
    await expect(page.locator('text=UPDATE')).toBeVisible();
    await expect(page.locator('text=DELETE')).toBeVisible();
  });

  test('should filter audit logs by user', async ({ page }) => {
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

    let filterApplied = false;
    await page.route('**/audit-logs', async route => {
      const url = new URL(route.request().url());
      const userId = url.searchParams.get('user_id');

      if (userId) filterApplied = true;

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            table_name: 'budget_item',
            record_id: 1,
            action: 'CREATE',
            user_id: 2,
            username: 'manager',
            timestamp: new Date().toISOString()
          }
        ])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/admin/audit');
    await page.waitForLoadState('networkidle');

    await page.selectOption('select[name="user_id"]', { label: 'manager' });
    await page.click('button:has-text("Apply Filter")');

    expect(filterApplied).toBe(true);
  });

  test('should filter audit logs by date range', async ({ page }) => {
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

    let dateFilterApplied = false;
    await page.route('**/audit-logs', async route => {
      const url = new URL(route.request().url());
      if (url.searchParams.get('start_date') || url.searchParams.get('end_date')) {
        dateFilterApplied = true;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/admin/audit');
    await page.waitForLoadState('networkidle');

    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[name="start_date"]', today);
    await page.fill('input[name="end_date"]', today);
    await page.click('button:has-text("Apply")');

    expect(dateFilterApplied).toBe(true);
  });

  test('should expand to see old/new values diff', async ({ page }) => {
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

    await page.route('**/audit-logs', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 2,
            table_name: 'budget_item',
            record_id: 1,
            action: 'UPDATE',
            user_id: 1,
            username: 'admin',
            old_values: { title: 'Old Title', budget_amount: 50000 },
            new_values: { title: 'New Title', budget_amount: 75000 },
            timestamp: new Date().toISOString()
          }
        ])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/admin/audit');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("View Details")');
    await page.waitForTimeout(500);

    await expect(page.locator('text=Old Title')).toBeVisible();
    await expect(page.locator('text=New Title')).toBeVisible();
    await expect(page.locator('text=50000')).toBeVisible();
    await expect(page.locator('text=75000')).toBeVisible();
  });

  test('Manager cannot access audit logs', async ({ page }) => {
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

    await page.route('**/audit-logs', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Insufficient permissions' })
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'manager');
    await page.fill('#password', 'manager123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/admin/audit');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=/403|Forbidden|Access Denied/i')).toBeVisible();
  });
});
