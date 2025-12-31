import { test, expect } from '@playwright/test';

test.describe('UI/UX Feedback', () => {

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

  test('should show loading spinner during API calls', async ({ page }) => {
    await page.route('**/budget-items', async route => {
      await page.waitForTimeout(1000);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/budget-items');

    await expect(page.locator('.loading-spinner, .spinner, text=Loading...')).toBeVisible({ timeout: 500 });

    await page.waitForLoadState('networkidle');

    await expect(page.locator('.loading-spinner, .spinner')).not.toBeVisible();
  });

  test('should show toast notification on success', async ({ page }) => {
    let successToastShown = false;

    page.on('dialog', async dialog => {
      if (dialog.message().includes('success') || dialog.message().includes('created') || dialog.message().includes('updated')) {
        successToastShown = true;
      }
      await dialog.accept();
    });

    await page.route('**/groups', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.route('**/user-groups', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            name: 'New Group',
            description: 'Created via test'
          })
        });
      }
    });

    await page.goto('/admin/groups');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Create Group")');
    await page.waitForTimeout(300);

    await page.fill('input[name="name"]', 'New Group');
    await page.fill('input[name="description"]', 'Created via test');
    await page.click('button:has-text("Save")');

    await page.waitForTimeout(1000);

    const toast = page.locator('.toast, .notification, text=success');
    await expect(toast.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show error notification on API failure', async ({ page }) => {
    await page.route('**/budget-items', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Duplicate workday reference' })
        });
      }
    });

    await page.route('**/groups', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, name: 'Finance' }])
      });
    });

    await page.goto('/budget-items');
    await page.click('button:has-text("Create Budget Item")');
    await page.waitForTimeout(300);

    await page.fill('input[placeholder*="WD-"]', 'WD-EXISTING');
    await page.fill('input[placeholder*="Title"]', 'Test Budget');
    await page.fill('input[type="number"]', '100000');

    await page.click('button:has-text("Create")');
    await page.waitForTimeout(1000);

    await expect(page.locator('text=/error|failed|duplicate/i')).toBeVisible({ timeout: 5000 });
  });

  test('should disable form submit button during submission', async ({ page }) => {
    await page.route('**/budget-items', async route => {
      if (route.request().method() === 'POST') {
        await page.waitForTimeout(1500);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            workday_ref: 'WD-001',
            title: 'Test',
            budget_amount: 100000,
            currency: 'USD',
            fiscal_year: 2025,
            owner_group_id: 1
          })
        });
      }
    });

    await page.route('**/groups', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, name: 'Finance' }])
      });
    });

    await page.goto('/budget-items');
    await page.click('button:has-text("Create Budget Item")');
    await page.waitForTimeout(300);

    await page.fill('input[placeholder*="WD-"]', 'WD-001');
    await page.fill('input[placeholder*="Title"]', 'Test');
    await page.fill('input[type="number"]', '100000');

    const submitBtn = page.locator('button:has-text("Create")');
    await submitBtn.click();

    await expect(submitBtn).toHaveAttribute('disabled', '');
  });

  test('should maintain form state after validation error', async ({ page }) => {
    await page.route('**/groups', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, name: 'Finance' }])
      });
    });

    await page.route('**/budget-items', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Workday reference is required' })
        });
      }
    });

    await page.goto('/budget-items');
    await page.click('button:has-text("Create Budget Item")');
    await page.waitForTimeout(300);

    await page.fill('input[placeholder*="Title"]', 'My Budget');
    await page.fill('input[type="number"]', '100000');

    await page.click('button:has-text("Create")');
    await page.waitForTimeout(500);

    await page.fill('input[placeholder*="WD-"]', 'WD-NOW-VALID');
    await page.click('button:has-text("Create")');

    await expect(page.locator('input[value="WD-NOW-VALID"]')).toHaveValue('WD-NOW-VALID');
    await expect(page.locator('input[value="My Budget"]')).toHaveValue('My Budget');
  });
});
