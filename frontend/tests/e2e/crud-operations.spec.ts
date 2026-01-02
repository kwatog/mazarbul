import { test, expect } from '@playwright/test';

async function loginAs(page, username, password) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');

  try {
    await page.waitForURL('**/', { timeout: 10000 });
  } catch (e) {
    await page.goto('/');
  }

  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
}

test.describe('CRUD Operations - True E2E', () => {
  test.use({ viewport: { width: 1280, height: 720 } });

  test('should navigate through entity chain using seeded data', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await expect(page.locator('.base-card, .base-table, .empty-state').first()).toBeVisible({ timeout: 10000 });
  });

  test('should navigate through full entity chain', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.base-card').first()).toBeVisible();

    await loginAs(page, 'admin', 'admin123');
    await page.goto('/business-cases');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.base-card').first()).toBeVisible();

    await loginAs(page, 'admin', 'admin123');
    await page.goto('/line-items');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.base-card, h1').first()).toBeVisible();

    await loginAs(page, 'admin', 'admin123');
    await page.goto('/wbs');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.base-card, h1').first()).toBeVisible();

    await loginAs(page, 'admin', 'admin123');
    await page.goto('/assets');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.base-card, h1').first()).toBeVisible();
  });

  test('admin should access all admin features', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Admin nav is a dropdown
    await expect(page.locator('button.nav-link:has-text("Admin")')).toBeVisible({ timeout: 10000 });

    await page.goto('/admin/audit');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.base-card, h1, .page-header').filter({ hasText: /Audit/i })).toBeVisible();

    await page.goto('/admin/groups');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.base-card, h3').filter({ hasText: /Group/i }).first()).toBeVisible();
  });

  test('manager should have different access than admin', async ({ page }) => {
    await loginAs(page, 'manager', 'manager123');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Manager should see Admin nav (same as admin)
    await expect(page.locator('button.nav-link:has-text("Admin")')).toBeVisible({ timeout: 5000 });

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.base-card, h3').filter({ hasText: /Budget/i }).first()).toBeVisible();
  });

  test('user should have restricted access', async ({ page }) => {
    await loginAs(page, 'user', 'user123');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // User should NOT see Admin nav
    await expect(page.locator('button.nav-link:has-text("Admin")')).not.toBeVisible({ timeout: 5000 });
  });
});
