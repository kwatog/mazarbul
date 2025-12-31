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

test.describe('CRUD Operations - True E2E', () => {
  test.use({ viewport: { width: 1280, height: 720 } });

  test('should navigate through entity chain using seeded data', async ({ page }) => {
    // Navigate to budget items - should show seeded budget item
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    // Seeded budget item should be visible
    await expect(adminPage.locator('table')).toBeVisible({ timeout: 10000 });
  });

  test('should navigate through full entity chain', async ({ page }) => {
    // Budget Items -> Business Cases -> Line Items -> WBS -> Assets
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.locator('h1:has-text("Budget Items")')).toBeVisible();

    await adminPage.goto('/business-cases');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.locator('h1:has-text("Business Cases")')).toBeVisible();

    await adminPage.goto('/line-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.locator('h1:has-text("Line Items")')).toBeVisible();

    await adminPage.goto('/wbs');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.locator('h1:has-text("Work Breakdown Structure")')).toBeVisible();

    await adminPage.goto('/assets');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.locator('h1:has-text("Assets")')).toBeVisible();
  });

  test('admin should access all admin features', async ({ page }) => {
    await adminPage.goto('/');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    // Admin should see admin panel
    await expect(adminPage.locator('text=Admin Panel')).toBeVisible({ timeout: 10000 });

    // Access audit logs
    await adminPage.goto('/admin/audit');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.locator('h1:has-text("Audit Logs")')).toBeVisible();

    // Access user groups
    await adminPage.goto('/admin/groups');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.locator('h1:has-text("User Groups")')).toBeVisible();
  });

  test('manager should have different access than admin', async ({ managerPage }) => {
    await managerPage.goto('/');
    await managerPage.waitForLoadState('networkidle');

    // Manager should NOT see admin panel
    await expect(managerPage.locator('text=Admin Panel')).not.toBeVisible({ timeout: 5000 });

    // But should still access regular features
    await managerPage.goto('/budget-items');
    await managerPage.waitForLoadState('networkidle');
    await expect(managerPage.locator('h1:has-text("Budget Items")')).toBeVisible();
  });

  test('user should have restricted access', async ({ userPage }) => {
    await userPage.goto('/');
    await userPage.waitForLoadState('networkidle');

    // User should NOT see admin panel
    await expect(userPage.locator('text=Admin Panel')).not.toBeVisible({ timeout: 5000 });
  });
});
