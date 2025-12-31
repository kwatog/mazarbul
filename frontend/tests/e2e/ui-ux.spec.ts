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

test.describe('UI/UX Feedback', () => {

  test('should show loading spinner during API calls', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    

    await expect(adminPage.locator('.loading-spinner, .spinner, text=Loading...')).toBeVisible({ timeout: 2000 });

    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.locator('.loading-spinner, .spinner')).not.toBeVisible();
  });

  test('should show toast notification on success', async ({ page }) => {
    let successToastShown = false;

    adminPage.on('dialog', async dialog => {
      if (dialog.message().includes('success') || dialog.message().includes('created') || dialog.message().includes('updated')) {
        successToastShown = true;
      }
      await dialog.accept();
    });

    await adminPage.goto('/admin/groups');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.click('button:has-text("Create Group")');
    await adminPage.waitForTimeout(300);

    await adminPage.fill('input[name="name"]', 'New Group');
    await adminPage.fill('input[name="description"]', 'Created via test');
    await adminPage.click('button:has-text("Save")');

    await adminPage.waitForTimeout(1000);

    const toast = adminPage.locator('.toast, .notification, text=success');
    await expect(toast.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show error notification on API failure', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.click('button:has-text("Create Budget Item")');
    await adminPage.waitForTimeout(300);

    await adminPage.fill('input[placeholder*="WD-"]', 'WD-EXISTING');
    await adminPage.fill('input[placeholder*="Title"]', 'Test Budget');
    await adminPage.fill('input[type="number"]', '100000');

    await adminPage.click('button:has-text("Create")');
    await adminPage.waitForTimeout(1000);

    await expect(adminPage.locator('text=/error|failed|duplicate/i')).toBeVisible({ timeout: 5000 });
  });

  test('should disable form submit button during submission', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.click('button:has-text("Create Budget Item")');
    await adminPage.waitForTimeout(300);

    await adminPage.fill('input[placeholder*="WD-"]', 'WD-001');
    await adminPage.fill('input[placeholder*="Title"]', 'Test');
    await adminPage.fill('input[type="number"]', '100000');

    const submitBtn = adminPage.locator('button:has-text("Create")');
    await submitBtn.click();

    await expect(submitBtn).toHaveAttribute('disabled', '');
  });

  test('should maintain form state after validation error', async ({ page }) => {
    await adminPage.goto('/budget-items');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.click('button:has-text("Create Budget Item")');
    await adminPage.waitForTimeout(300);

    await adminPage.fill('input[placeholder*="Title"]', 'My Budget');
    await adminPage.fill('input[type="number"]', '100000');

    await adminPage.click('button:has-text("Create")');
    await adminPage.waitForTimeout(500);

    await adminPage.fill('input[placeholder*="WD-"]', 'WD-NOW-VALID');
    await adminPage.click('button:has-text("Create")');

    await expect(adminPage.locator('input[value="WD-NOW-VALID"]')).toHaveValue('WD-NOW-VALID');
    await expect(adminPage.locator('input[value="My Budget"]')).toHaveValue('My Budget');
  });
});
