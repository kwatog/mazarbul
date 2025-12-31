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

test.describe('Budget to Business Case Workflow', () => {

  test('should create budget item successfully', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    

    await adminPage.click('button:has-text("Create Budget Item")');
    await adminPage.waitForTimeout(300);

    await adminPage.fill('input[placeholder*="WD-"]', 'WD-2025-TEST');
    await adminPage.fill('input[placeholder*="Title"]', 'IT Infrastructure Budget');
    await adminPage.fill('input[type="number"]', '100000');
    await adminPage.selectOption('select', { label: 'USD' });
    await adminPage.fill('input[placeholder*="2025"]', '2025');

    await adminPage.click('button:has-text("Create")');
    await adminPage.waitForTimeout(500);

    await expect(adminPage.locator('.modal-overlay')).not.toBeVisible();
  });

  test('should navigate through dashboard quick actions', async ({ page }) => {
    await adminPage.goto('/');
    await loginAs(page, 'admin', 'admin123');
    

    await expect(adminPage.locator('text=Total Budget')).toBeVisible();

    await adminPage.click('a[href="/budget-items"]');
    await expect(adminPage).toHaveURL('/budget-items');
  });

  test('should filter budget items by fiscal year', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.selectOption('select', { label: '2025' });
  });
});

test.describe('Purchase Order Workflow', () => {

  test('should display inherited owner group in PO form', async ({ managerPage }) => {
    await managerPage.goto('/purchase-orders');
    await managerPage.waitForLoadState('networkidle');

    await managerPage.click('button:has-text("Create PO")');
    await managerPage.waitForTimeout(300);

    await expect(managerPage.locator('text=Owner Group will be automatically inherited')).toBeVisible();
  });
});
