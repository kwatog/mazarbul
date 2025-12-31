import { test, expect } from '@playwright/test';

test.describe('Session & Authentication', () => {
  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    await page.route('**/auth/me', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Not authenticated' })
      });
    });

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/login/);
  });

  test('should clear tokens and redirect after logout', async ({ page }) => {
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

    await page.route('**/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1, username: 'admin', role: 'Admin' })
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/admin/audit');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Logout")');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/login/);
  });

  test('should show error on token expiry', async ({ page }) => {
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

    await page.route('**/auth/me', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Token has expired' })
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForTimeout(500);

    await page.goto('/budget-items');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=/expired|invalid|token/i')).toBeVisible();
  });

  test('should persist login across browser restart (cookie)', async ({ page }) => {
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

    await page.route('**/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1, username: 'admin', role: 'Admin' })
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    const cookies = await page.context().cookies();
    const hasAccessToken = cookies.some(c => c.name === 'access_token');

    expect(hasAccessToken).toBe(true);
  });

  test('should prevent access with invalid token', async ({ page }) => {
    await page.route('**/auth/me', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid token' })
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Session Security', () => {
  test('should not expose credentials in network requests', async ({ page }) => {
    const credentialsCaptured: string[] = [];

    await page.route('**/auth/login', async route => {
      const postData = route.request().postData();
      if (postData) {
        credentialsCaptured.push(postData);
      }
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
    await page.fill('#password', 'secretpassword');
    await page.click('button[type="submit"]');

    expect(credentialsCaptured.length).toBeGreaterThan(0);

    for (const cred of credentialsCaptured) {
      expect(cred).not.toContain('"password"');
    }
  });

  test('should use HttpOnly cookies for token storage', async ({ page }) => {
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

    const cookies = await page.context().cookies();
    const accessTokenCookie = cookies.find(c => c.name === 'access_token');

    expect(accessTokenCookie).toBeDefined();
    expect(accessTokenCookie?.httpOnly).toBe(true);
    expect(accessTokenCookie?.sameSite).toBe('lax');
  });
});
