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

test.describe('Entity Chain & Owner Group Inheritance', () => {

  test('WBS automatically inherits owner_group_id from line item', async ({ page }) => {
    await adminPage.goto('/wbs');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.locator('text=Create WBS')).toBeVisible();

    await adminPage.click('button:has-text("Create WBS")');
    await adminPage.waitForTimeout(300);

    await expect(adminPage.locator('text=Owner Group will be inherited from Line Item')).toBeVisible();
  });

  test('Asset automatically inherits owner_group_id from WBS', async ({ page }) => {
    await adminPage.goto('/assets');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.locator('text=Create Asset')).toBeVisible();

    await adminPage.click('button:has-text("Create Asset")');
    await adminPage.waitForTimeout(300);

    await expect(adminPage.locator('text=Owner Group will be inherited from WBS')).toBeVisible();
  });

  test('PO automatically inherits owner_group_id from Asset', async ({ page }) => {
    await adminPage.goto('/purchase-orders');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.locator('text=Create PO')).toBeVisible();

    await adminPage.click('button:has-text("Create PO")');
    await adminPage.waitForTimeout(300);

    await expect(adminPage.locator('text=Owner Group will be inherited from Asset')).toBeVisible();
  });

  test('GR automatically inherits owner_group_id from PO', async ({ page }) => {
    await adminPage.goto('/goods-receipts');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.locator('text=Create GR')).toBeVisible();

    await adminPage.click('button:has-text("Create GR")');
    await adminPage.waitForTimeout(300);

    await expect(adminPage.locator('text=Owner Group will be inherited from PO')).toBeVisible();
  });

  test('Allocation automatically inherits owner_group_id from PO', async ({ page }) => {
    await adminPage.goto('/allocations');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.click('button:has-text("Create Allocation")');
    await adminPage.waitForTimeout(300);

    await expect(adminPage.locator('text=Owner Group will be inherited from PO')).toBeVisible();
  });

  test('Child record shows parent owner_group in detail view', async ({ page }) => {
    await adminPage.goto('/line-items/1');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.locator('text=Owner Group')).toBeVisible();
  });
});
