import { test, expect } from '@playwright/test';

test.describe('App Workspace', () => {
  test('should display welcome message and module cards', async ({ page }) => {
    // Navigate to the app page (using HashRouter)
    await page.goto('/#/app');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check welcome heading
    await expect(page.getByRole('heading', { name: /Welcome to The Planner's Assistant/i })).toBeVisible();

    // Check description
    await expect(page.getByText(/Your comprehensive toolkit for modern urban and regional planning/i)).toBeVisible();

    // Check all 6 module cards are present with correct titles
    const modules = [
      'Evidence Base',
      'Vision & Concepts',
      'Policy Drafter',
      'Strategy Modeler',
      'Site Assessment',
      'Feedback Analysis',
    ];

    for (const module of modules) {
      // Use role='button' to specifically target the module cards
      await expect(page.getByRole('button', { name: new RegExp(module, 'i') })).toBeVisible();
    }
  });

  test('should allow selecting a module and show prompt interface', async ({ page }) => {
    await page.goto('/#/app');
    await page.waitForLoadState('networkidle');

    // Click on Evidence Base module
    await page.getByText('Evidence Base', { exact: true }).click();

    // Should show the prompt textarea (check for textarea element)
    await expect(page.locator('textarea').first()).toBeVisible();

    // Should show Run Analysis button
    await expect(page.getByRole('button', { name: /Run Analysis/i })).toBeVisible();

  // Should show example prompts section
  await expect(page.getByText(/Try an example/i)).toBeVisible();
  });

  test('should handle module switching correctly', async ({ page }) => {
    await page.goto('/#/app');
    await page.waitForLoadState('networkidle');

    // Select Evidence Base
    await page.getByText('Evidence Base', { exact: true }).click();
    await expect(page.getByText('Evidence Base', { exact: true }).first()).toBeVisible();

    // Switch to Policy Drafter
    await page.getByText('Policy Drafter', { exact: true }).click();
    
    // Should show Policy Drafter selected
    await page.waitForTimeout(500); // Allow animation to complete
    const policyModule = page.getByText('Policy Drafter', { exact: true }).first();
    await expect(policyModule).toBeVisible();
  });

  test('should not have console errors on load', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/#/app');
    await page.waitForLoadState('networkidle');
    
    // Wait a bit for any async errors
    await page.waitForTimeout(2000);

    // Filter out expected warnings (Tailwind CDN warning is expected until we migrate)
    const unexpectedErrors = consoleErrors.filter(
      (err) => !err.includes('tailwindcss.com') && !err.includes('production')
    );

    expect(unexpectedErrors).toHaveLength(0);
  });

  test('should show empty state in results panel initially', async ({ page }) => {
    await page.goto('/#/app');
    await page.waitForLoadState('networkidle');
    
    // Select a module
    await page.getByText('Evidence Base', { exact: true }).click();

    // Should show empty state message
    await expect(page.getByText(/Ready to Analyze/i)).toBeVisible();
    await expect(page.getByText(/Enter your planning query on the left and click/i)).toBeVisible();
  });

  test('auto-routes ask box to best tool', async ({ page }) => {
    await page.goto('/#/app');
    const askInput = page.locator('#ask-text');
    await askInput.fill('Draft a policy for sustainable transport in new developments');
    await askInput.press('Enter');
    // Header should switch to the selected tool automatically
    await expect(page.getByRole('heading', { name: /Policy Drafter/ })).toBeVisible();
  });

  test('detects coordinates and reveals site inputs', async ({ page }) => {
    await page.goto('/#/app');
    const askInput = page.locator('#ask-text');
    await askInput.fill('Site assessment at 51.5074, -0.1278 for residential development');
    await askInput.press('Enter');
    // Should route to Site Assessment (dm) and show site inputs prefilled
    await expect(page.getByRole('heading', { name: /Site Assessment/ })).toBeVisible();
    const latInput = page.getByPlaceholder('Latitude');
    const lngInput = page.getByPlaceholder('Longitude');
    await expect(latInput).toHaveValue(/51\.5074/);
    await expect(lngInput).toHaveValue(/-0\.1278/);
  });
});
