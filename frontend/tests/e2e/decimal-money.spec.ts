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

test.describe('Decimal Money Handling', () => {

  test('should display currency with 2 decimal places', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    const budgetCell = adminPage.locator('table tbody tr:first-child td:nth-child(4)');
    await expect(budgetCell).toContainText('.00');
  });

  test('should display currency with proper formatting (comma separators)', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    const budgetCell = adminPage.locator('table tbody tr:first-child td:nth-child(4)');
    await expect(budgetCell).toContainText(',');
  });

  test('should handle zero values correctly', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.locator('text=0.00')).toBeVisible();
  });
});
