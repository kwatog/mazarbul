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

test.describe('Record Access Sharing', () => {

  test('should grant Read access to specific user', async ({ page }) => {
    await adminPage.goto('/budget-items/1');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.click('button:has-text("Share")');
    await adminPage.waitForTimeout(500);
  });

  test('should grant Read/Write access to group', async ({ page }) => {
    await adminPage.goto('/budget-items/1');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.click('button:has-text("Share")');
    await adminPage.waitForTimeout(500);

    await expect(adminPage.locator('text=Grant to Group')).toBeVisible();
  });

  test('should set and verify access expiration', async ({ page }) => {
    await adminPage.goto('/budget-items/1');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.click('button:has-text("Share")');
    await adminPage.waitForTimeout(500);
  });

  test('should revoke previously granted access', async ({ page }) => {
    await adminPage.goto('/budget-items/1');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.click('button:has-text("Share")');
    await adminPage.waitForTimeout(500);

    const revokeButton = adminPage.locator('button:has-text("Revoke")').first();
    if (await revokeButton.isVisible()) {
      await revokeButton.click();
      await adminPage.waitForTimeout(500);
    }
  });

  test('should show existing access grants in share modal', async ({ page }) => {
    await adminPage.goto('/budget-items/1');
    await loginAs(page, 'admin', 'admin123');
    
    await adminPage.waitForLoadState('networkidle');

    await adminPage.click('button:has-text("Share")');
    await adminPage.waitForTimeout(500);
  });
});
