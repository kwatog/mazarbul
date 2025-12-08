import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('should login successfully and redirect to home', async ({ page }) => {
    // Mock the login API call
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Login successful',
          user: { id: 1, username: 'testuser', role: 'admin' }
        })
      });
    });

    await page.goto('/login');
    
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'password123');
    await page.click('button[type="submit"]');

    // Wait for navigation
    await expect(page).toHaveURL('/');
  });

  test('should show error on failed login', async ({ page }) => {
    // Mock the login API call to fail
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' })
      });
    });

    await page.goto('/login');
    
    await page.fill('#username', 'wronguser');
    await page.fill('#password', 'wrongpass');
    await page.click('button[type="submit"]');

    // Verify error message
    await expect(page.locator('.error-message')).toContainText('Invalid credentials');
    await expect(page).toHaveURL('/login');
  });
});
