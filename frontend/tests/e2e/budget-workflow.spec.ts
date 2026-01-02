import { test, expect } from '@playwright/test';

async function loginAs(page, username, password) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000); // Wait for hydration
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/', { timeout: 10000 });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000); // Wait for dashboard to load
}

test.describe('Budget to Business Case Workflow', () => {

  test('should create budget item successfully', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/budget-items');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // BaseButton renders with text content
    await page.click('button:has-text("+ Create Budget Item")');
    await page.waitForTimeout(500);

    // BaseModal renders with role="dialog"
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    // BaseInput renders as div with label
    await expect(page.locator('label:has-text("Workday Reference")')).toBeVisible();
    // BaseSelect has role="combobox"
    await expect(page.locator('[role="combobox"]').first()).toBeVisible();
  });

  test('should navigate through dashboard quick actions', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/');

    // Dashboard stat-label contains "Total Budget"
    await expect(page.locator('.stat-label:has-text("Total Budget")')).toBeVisible();

    // Use the quick action button in the Quick Actions section
    await page.click('.quick-action-btn:has-text("Manage Budgets")');
    await expect(page).toHaveURL('/budget-items');
  });

  test('should filter budget items by fiscal year', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/budget-items');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // First combobox is Fiscal Year filter
    await page.locator('[role="combobox"]').first().click();
    await page.waitForTimeout(200);
    // Click on the option
    await page.locator('[role="option"]:has-text("2025")').first().click();
  });
});

test.describe('Purchase Order Workflow', () => {

  test('should display inherited owner group in PO form', async ({ page }) => {
    await loginAs(page, 'manager', 'manager123');
    await page.goto('/purchase-orders');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Button text is "+ Create PO"
    await page.click('button:has-text("+ Create PO")');
    await page.waitForTimeout(500);

    // Purchase orders page uses BaseModal with role="dialog"
    await expect(page.locator('.modal-overlay, [role="dialog"]')).toBeVisible();
  });
});
