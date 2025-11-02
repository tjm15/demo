import { test, expect } from '@playwright/test';

test.describe('Planner App UI', () => {
  test('loads app route and shows welcome and modules', async ({ page }) => {
    await page.goto('/#/app');
    await expect(page.getByRole('heading', { name: "Welcome to The Planner's Assistant" })).toBeVisible();
    // Check tool cards exist (by button accessible name)
    await expect(page.getByRole('button', { name: /Evidence Base/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Vision & Concepts/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Policy Drafter/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Strategy Modeler/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Site Assessment/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Feedback Analysis/ })).toBeVisible();
  });

  test('auto-classifies question and routes to Strategy Modeler', async ({ page }) => {
    await page.goto('/#/app');
    const input = page.locator('#ask-text');
    await input.fill('Compare urban extension vs brownfield intensification for 5000 homes');
    await input.press('Enter');
    // Header should show Strategy Modeler
    await expect(page.getByRole('heading', { level: 2, name: /Strategy Modeler/ })).toBeVisible();
    // The textarea should contain our question
    await expect(page.locator('textarea')).toHaveValue(/urban extension|brownfield/i);
  });
  test('clicks example prompt and populates textarea', async ({ page }) => {
    await page.goto('/#/app');
    // Switch to Evidence Base to ensure different examples
    await page.getByText('Evidence Base').click();
    const exampleButton = page.getByRole('button', { name: /Site at .* for residential development|Brownfield site near town center/ });
    await exampleButton.first().click();
    const textarea = page.locator('textarea');
    await expect(textarea).toHaveValue(/Site at|Brownfield site/);
  });
});
