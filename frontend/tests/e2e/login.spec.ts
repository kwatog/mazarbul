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

test.describe('Login Flow', () => {
  test('should login successfully with admin credentials', async ({ page }) => {
    const responses: string[] = [];

    page.on('response', async (response) => {
      if (response.url().includes('/auth/login')) {
        responses.push(`${response.status()}`);
      }
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForTimeout(2000);

    expect(responses).toContain('200');
  });

  test('should show error on failed login with wrong credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('#username', 'wronguser');
    await page.fill('#password', 'wrongpass');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error-message')).toContainText('Incorrect username or password', { timeout: 5000 });
    await expect(page).toHaveURL('/login');
  });

  test('admin user should see admin navigation items', async ({ page }) => {
    await loginAs(page, 'admin', 'admin123');
    await page.goto('/');

    await expect(page.locator('text=Admin Panel')).toBeVisible({ timeout: 10000 });
  });

  test('manager user should not see admin navigation items', async ({ page }) => {
    await loginAs(page, 'manager', 'manager123');
    await page.goto('/');

    await expect(page.locator('text=Admin Panel')).not.toBeVisible({ timeout: 5000 });
  });

  test('regular user should not see admin navigation items', async ({ page }) => {
    await loginAs(page, 'user', 'user123');
    await page.goto('/');

    await expect(page.locator('text=Admin Panel')).not.toBeVisible({ timeout: 5000 });
  });
});
