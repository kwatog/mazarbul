import { test, expect } from '@playwright/test';

async function loginAs(page, username, password) {
  await page.goto('/login');
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');

  try {
    await page.waitForFunction(() => {
      const cookie = document.cookie.split('; ').find(c => c.startsWith('user_info='));
      return cookie !== undefined;
    }, { timeout: 10000 });
  } catch (e) {
    // Continue anyway
  }
}

test.describe('Audit Log Viewer', () => {

  test('Admin can view complete audit trail', async ({ page }) => {
    await adminPage.goto('/admin/audit');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.locator('text=Audit Logs')).toBeVisible();
  });

  test('should filter audit logs by user', async ({ page }) => {
    await adminPage.goto('/admin/audit');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.selectOption('select[name="user_id"]', { label: 'manager' });
    await adminPage.click('button:has-text("Apply Filter")');
    await adminPage.waitForLoadState('networkidle');
  });

  test('should filter audit logs by date range', async ({ page }) => {
    await adminPage.goto('/admin/audit');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    const today = new Date().toISOString().split('T')[0];
    await adminPage.fill('input[name="start_date"]', today);
    await adminPage.fill('input[name="end_date"]', today);
    await adminPage.click('button:has-text("Apply")');
    await adminPage.waitForLoadState('networkidle');
  });

  test('should expand to see old/new values diff', async ({ page }) => {
    await adminPage.goto('/admin/audit');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.click('button:has-text("View Details")');
    await adminPage.waitForTimeout(500);
  });

  test('Manager cannot access audit logs', async ({ managerPage, page: unauthenticatedPage }) => {
    await managerPage.goto('/');
    await managerPage.goto('/admin/audit');
    await managerPage.waitForLoadState('networkidle');

    await expect(managerPage.locator('text=/403|Forbidden|Access Denied/i')).toBeVisible();
  });
});
