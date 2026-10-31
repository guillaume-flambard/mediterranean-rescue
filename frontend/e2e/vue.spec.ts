import { test, expect } from '@playwright/test'

// Test de bout en bout dans un vrai navigateur (`pnpm test:e2e`). Il faut que l'API Django
// tourne avec les données fictives chargées (voir README.md).
test('shows the published operations', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('h1')).toHaveText('SOS MEDITERRANEE operations')
  await expect(page.getByRole('status')).toHaveText('4 published operations')
})
