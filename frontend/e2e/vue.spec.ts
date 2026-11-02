import { test, expect } from '@playwright/test'

// Test de bout en bout dans un vrai navigateur (`pnpm test:e2e`).
// Pour commencer : https://playwright.dev/docs/intro
test('visits the app root url', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('h1')).toHaveText('La carte des opérations de SOS MEDITERRANEE')
})
