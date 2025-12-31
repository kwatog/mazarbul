import { test, expect } from '@playwright/test';

test.describe('Entity Chain & Owner Group Inheritance', () => {

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

  test('WBS automatically inherits owner_group_id from line item', async ({ page }) => {
    await page.route('**/business-case-line-items', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            title: 'Line Item 1',
            business_case_id: 1,
            budget_item_id: 1,
            owner_group_id: 5,
            requested_amount: 50000
          }
        ])
      });
    });

    await page.route('**/wbs', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            business_case_line_item_id: 1,
            wbs_code: 'WBS-001',
            owner_group_id: 5,
            description: 'Auto-inherited from line item'
          }
        ])
      });
    });

    await page.goto('/wbs');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=WBS-001')).toBeVisible();

    await page.click('button:has-text("Create WBS")');
    await page.waitForTimeout(300);

    await expect(page.locator('text=Owner Group will be inherited from Line Item')).toBeVisible();
  });

  test('Asset automatically inherits owner_group_id from WBS', async ({ page }) => {
    await page.route('**/wbs', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            wbs_code: 'WBS-001',
            owner_group_id: 7,
            business_case_line_item_id: 1
          }
        ])
      });
    });

    await page.route('**/assets', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            wbs_id: 1,
            asset_code: 'ASSET-001',
            owner_group_id: 7,
            description: 'Auto-inherited from WBS'
          }
        ])
      });
    });

    await page.goto('/assets');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=ASSET-001')).toBeVisible();

    await page.click('button:has-text("Create Asset")');
    await page.waitForTimeout(300);

    await expect(page.locator('text=Owner Group will be inherited from WBS')).toBeVisible();
  });

  test('PO automatically inherits owner_group_id from Asset', async ({ page }) => {
    await page.route('**/assets', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            asset_code: 'ASSET-001',
            owner_group_id: 3,
            wbs_id: 1
          }
        ])
      });
    });

    await page.route('**/purchase-orders', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            asset_id: 1,
            po_number: 'PO-001',
            owner_group_id: 3,
            total_amount: 25000
          }
        ])
      });
    });

    await page.goto('/purchase-orders');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=PO-001')).toBeVisible();

    await page.click('button:has-text("Create PO")');
    await page.waitForTimeout(300);

    await expect(page.locator('text=Owner Group will be inherited from Asset')).toBeVisible();
  });

  test('GR automatically inherits owner_group_id from PO', async ({ page }) => {
    await page.route('**/purchase-orders', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            po_number: 'PO-001',
            owner_group_id: 2,
            asset_id: 1,
            total_amount: 10000
          }
        ])
      });
    });

    await page.route('**/goods-receipts', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            po_id: 1,
            gr_number: 'GR-001',
            owner_group_id: 2,
            amount: 5000
          }
        ])
      });
    });

    await page.goto('/goods-receipts');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=GR-001')).toBeVisible();

    await page.click('button:has-text("Create GR")');
    await page.waitForTimeout(300);

    await expect(page.locator('text=Owner Group will be inherited from PO')).toBeVisible();
  });

  test('Allocation automatically inherits owner_group_id from PO', async ({ page }) => {
    await page.route('**/purchase-orders', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            po_number: 'PO-001',
            owner_group_id: 4,
            asset_id: 1,
            total_amount: 50000
          }
        ])
      });
    });

    await page.route('**/resources', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: 'Developer', cost_per_month: 10000, owner_group_id: 4 }
        ])
      });
    });

    await page.route('**/allocations', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            resource_id: 1,
            po_id: 1,
            owner_group_id: 4,
            expected_monthly_burn: 10000
          }
        ])
      });
    });

    await page.goto('/allocations');
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Create Allocation")');
    await page.waitForTimeout(300);

    await expect(page.locator('text=Owner Group will be inherited from PO')).toBeVisible();
  });

  test('Child record shows parent owner_group in detail view', async ({ page }) => {
    await page.route('**/business-case-line-items', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            title: 'Parent Line Item',
            owner_group_id: 10,
            business_case_id: 1,
            budget_item_id: 1
          }
        ])
      });
    });

    await page.route('**/business-case-line-items/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          title: 'Parent Line Item',
          owner_group_id: 10,
          business_case_id: 1,
          budget_item_id: 1
        })
      });
    });

    await page.goto('/line-items/1');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Owner Group')).toBeVisible();
  });
});
