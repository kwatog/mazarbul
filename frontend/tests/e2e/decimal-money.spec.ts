import { test, expect } from '@playwright/test';

test.describe('Decimal Money Handling', () => {

  test.beforeEach(async ({ page }) => {
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
  });

  test('should display currency with 2 decimal places', async ({ page }) => {
    await page.route('**/budget-items', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            workday_ref: 'WD-001',
            title: 'Precision Test',
            budget_amount: '100000.00',
            currency: 'USD',
            fiscal_year: 2025,
            owner_group_id: 1
          }
        ])
      });
    });

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=WD-001')).toBeVisible();

    const budgetCell = page.locator('table tbody tr:first-child td:nth-child(4)');
    await expect(budgetCell).toContainText('100000.00');
  });

  test('should round currency values to 2dp on input', async ({ page }) => {
    await page.route('**/groups', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, name: 'Finance' }])
      });
    });

    await page.route('**/budget-items', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            workday_ref: 'WD-001',
            title: 'Rounded Budget',
            budget_amount: '123456.78',
            currency: 'USD',
            fiscal_year: 2025,
            owner_group_id: 1
          })
        });
      }
    });

    await page.goto('/budget-items');
    await page.click('button:has-text("Create Budget Item")');
    await page.waitForTimeout(300);

    await page.fill('input[placeholder*="WD-"]', 'WD-001');
    await page.fill('input[placeholder*="Title"]', 'Rounded Budget');

    await page.fill('input[type="number"]', '123456.789');

    await page.click('button:has-text("Create")');
    await page.waitForTimeout(500);

    const postData = await page.request.postData();
    expect(postData).toContain('123456.78');
  });

  test('should display currency with proper formatting (comma separators)', async ({ page }) => {
    await page.route('**/budget-items', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            workday_ref: 'WD-001',
            title: 'Large Budget',
            budget_amount: '1000000.00',
            currency: 'USD',
            fiscal_year: 2025,
            owner_group_id: 1
          }
        ])
      });
    });

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');

    const budgetCell = page.locator('table tbody tr:first-child td:nth-child(4)');
    await expect(budgetCell).toContainText('1,000,000.00');
  });

  test('should handle zero values correctly', async ({ page }) => {
    await page.route('**/budget-items', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            workday_ref: 'WD-001',
            title: 'Zero Budget',
            budget_amount: '0.00',
            currency: 'USD',
            fiscal_year: 2025,
            owner_group_id: 1
          }
        ])
      });
    });

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Zero Budget')).toBeVisible();
    await expect(page.locator('text=0.00')).toBeVisible();
  });
});
