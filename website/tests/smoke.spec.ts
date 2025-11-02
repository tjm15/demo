import { test, expect } from '@playwright/test';

test('landing copy and module cards render', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByText('Welcome to The Planner\'s Assistant')).toBeVisible();
  await expect(page.getByText('Your comprehensive toolkit for modern urban and regional planning. Select a tool below to get started.')).toBeVisible();

  // Check that the six module cards are visible
  const labels = [
    'Evidence Base',
    'Vision & Concepts',
    'Policy Drafter',
    'Strategy Modeler',
    'Site Assessment',
    'Feedback Analysis',
  ];
  for (const label of labels) {
    await expect(page.getByText(label)).toBeVisible();
  }
});
