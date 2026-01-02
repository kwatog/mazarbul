import { test } from '@playwright/test';

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

test.describe('Application Screenshots', () => {

  test('01-login-page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/01-login-page.png', fullPage: true });
  });

  test('02-dashboard', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/02-dashboard.png', fullPage: true });
  });

  test('03-budget-items-list', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/03-budget-items-list.png', fullPage: true });
  });

  test('04-budget-items-create-modal', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("+ Create Budget Item")');
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/04-budget-items-create-modal.png', fullPage: true });
  });

  test('05-purchase-orders', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/purchase-orders');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/05-purchase-orders.png', fullPage: true });
  });

  test('05b-purchase-orders-create-modal', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/purchase-orders');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("+ Create PO")');
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/05b-purchase-orders-create-modal.png', fullPage: true });
  });

  test('06-wbs', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/wbs');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/06-wbs.png', fullPage: true });
  });

  test('06b-wbs-create-modal', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/wbs');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("+ Create WBS")');
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/06b-wbs-create-modal.png', fullPage: true });
  });

  test('07-assets', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/assets');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/07-assets.png', fullPage: true });
  });

  test('07b-assets-create-modal', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/assets');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("+ Create Asset")');
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/07b-assets-create-modal.png', fullPage: true });
  });

  test('08-admin-groups', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/admin/groups');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/08-admin-groups.png', fullPage: true });
  });

  test('09-admin-audit', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/admin/audit');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/09-admin-audit.png', fullPage: true });
  });

  test('10-business-cases', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/business-cases');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/10-business-cases.png', fullPage: true });
  });

  test('11-goods-receipts', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/goods-receipts');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/11-goods-receipts.png', fullPage: true });
  });

  test('11b-goods-receipts-create-modal', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/goods-receipts');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("+ Create GR")');
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/11b-goods-receipts-create-modal.png', fullPage: true });
  });
});
