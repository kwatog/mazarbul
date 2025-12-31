import { test, expect } from '@playwright/test';

test.describe('Record Access Sharing', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should grant Read access to specific user', async ({ page }) => {
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

    await page.route('**/budget-items/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          workday_ref: 'WD-001',
          title: 'Shareable Budget',
          budget_amount: 100000,
          currency: 'USD',
          fiscal_year: 2025,
          owner_group_id: 1,
          created_by: 1
        })
      });
    });

    await page.route('**/users', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 2, username: 'user1', full_name: 'User One' },
          { id: 3, username: 'user2', full_name: 'User Two' }
        ])
      });
    });

    await page.route('**/record-access', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.route('**/record-access', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            record_type: 'BudgetItem',
            record_id: 1,
            user_id: 2,
            access_level: 'Read',
            granted_by: 1
          })
        });
      }
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/budget-items/1');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Share")');
    await page.waitForTimeout(500);

    await page.selectOption('select[name="user_id"]', { label: 'User One' });
    await page.selectOption('select[name="access_level"]', { label: 'Read' });
    await page.click('button:has-text("Grant")');
    await page.waitForTimeout(500);

    await expect(page.locator('text=Read granted successfully')).toBeVisible();
  });

  test('should grant Read/Write access to group', async ({ page }) => {
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

    await page.route('**/budget-items/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          workday_ref: 'WD-001',
          title: 'Shareable Budget',
          budget_amount: 100000,
          fiscal_year: 2025,
          owner_group_id: 1,
          created_by: 1
        })
      });
    });

    await page.route('**/user-groups', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: 'Engineering Team' },
          { id: 2, name: 'Finance Team' }
        ])
      });
    });

    await page.route('**/record-access', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/budget-items/1');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Share")');
    await page.waitForTimeout(500);

    await expect(page.locator('text=Grant to Group')).toBeVisible();
  });

  test('should set and verify access expiration', async ({ page }) => {
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

    await page.route('**/budget-items/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          workday_ref: 'WD-001',
          title: 'Temporary Access Budget',
          budget_amount: 100000,
          fiscal_year: 2025,
          owner_group_id: 1,
          created_by: 1
        })
      });
    });

    await page.route('**/users', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 2, username: 'tempuser', full_name: 'Temp User' }
        ])
      });
    });

    await page.route('**/record-access', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/budget-items/1');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Share")');
    await page.waitForTimeout(500);

    await page.selectOption('select[name="user_id"]', { label: 'Temp User' });
    await page.selectOption('select[name="access_level"]', { label: 'Write' });

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toISOString().split('T')[0];

    await page.fill('input[type="date"]', dateStr);
    await page.click('button:has-text("Grant")');
    await page.waitForTimeout(500);

    await expect(page.locator('text=expires')).toBeVisible();
  });

  test('should revoke previously granted access', async ({ page }) => {
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

    await page.route('**/budget-items/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          workday_ref: 'WD-001',
          title: 'Revokable Budget',
          budget_amount: 100000,
          fiscal_year: 2025,
          owner_group_id: 1,
          created_by: 1
        })
      });
    });

    await page.route('**/record-access', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            record_type: 'BudgetItem',
            record_id: 1,
            user_id: 2,
            username: 'user1',
            access_level: 'Read',
            granted_by: 1
          }
        ])
      });
    });

    await page.route('**/record-access/1', async route => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Access revoked' })
        });
      }
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/budget-items/1');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Share")');
    await page.waitForTimeout(500);

    await expect(page.locator('text=user1')).toBeVisible();
    await expect(page.locator('text=Read')).toBeVisible();

    await page.click('button:has-text("Revoke")');
    await page.waitForTimeout(500);

    await expect(page.locator('text=user1')).not.toBeVisible();
  });

  test('should show existing access grants in share modal', async ({ page }) => {
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

    await page.route('**/budget-items/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          workday_ref: 'WD-001',
          title: 'Multi-Access Budget',
          budget_amount: 100000,
          fiscal_year: 2025,
          owner_group_id: 1,
          created_by: 1
        })
      });
    });

    await page.route('**/record-access', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, username: 'user1', access_level: 'Read', expires_at: null },
          { id: 2, username: 'user2', access_level: 'Write', expires_at: null },
          { id: 3, group_name: 'Engineering', access_level: 'Read', expires_at: null }
        ])
      });
    });

    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    await page.goto('/budget-items/1');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Share")');
    await page.waitForTimeout(500);

    await expect(page.locator('text=user1')).toBeVisible();
    await expect(page.locator('text=user2')).toBeVisible();
    await expect(page.locator('text=Engineering')).toBeVisible();
    await expect(page.locator('text=Read').first()).toBeVisible();
    await expect(page.locator('text=Write').first()).toBeVisible();
  });
});
