import { expect, test } from '@playwright/test'
import type { Inquiry } from '../src/api'

// All mutation tests intercept the API. They never update the real database.
const original: Inquiry = {
  id: '00000000-0000-0000-0000-000000000007', customer_name: 'Status Browser Test',
  email: 'status-test@example.com', message: 'Please review my request.', category: 'support',
  priority: 'high', status: 'new', ai_summary: 'Customer requests a review.',
  created_at: '2026-01-01T12:00:00Z',
}

test('status controls save once, refresh filters, resolve, and reopen', async ({ page }) => {
  let record = { ...original }
  let release!: () => void
  const gate = new Promise<void>((resolve) => { release = resolve })
  let writes = 0
  await page.route(`**/api/v1/inquiries/${record.id}`, (route) => route.fulfill({ json: record }))
  await page.route('**/api/v1/inquiries/page?*', (route) => {
    const matches = new URL(route.request().url()).searchParams.get('status') === record.status
    return route.fulfill({ json: { items: matches ? [record] : [], total: matches ? 1 : 0, limit: 20, offset: 0 } })
  })
  await page.route(`**/api/v1/inquiries/${record.id}/status`, async (route) => {
    expect(route.request().method()).toBe('PATCH')
    const body = route.request().postDataJSON()
    expect(body.expected_status).toBe(record.status)
    writes++
    if (writes === 1) await gate
    record = { ...record, status: body.status }
    await route.fulfill({ json: record })
  })
  await page.goto(`/inquiries?status=new&selected=${record.id}`)
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByRole('heading', { name: 'AI Insights' })).toBeVisible()
  await expect(dialog.getByText('Classification and summary stored')).toBeVisible()
  await dialog.getByRole('button', { name: 'Start progress' }).click()
  await expect(dialog.getByRole('button', { name: 'Saving…' })).toBeDisabled()
  release()
  await expect(dialog.getByRole('status')).toContainText('Status updated to In progress.')
  await expect(page).toHaveURL(new RegExp(`selected=${record.id}`))
  await dialog.getByRole('button', { name: 'Mark resolved' }).click()
  await expect(dialog.getByRole('status')).toContainText('Status updated to Resolved.')
  await dialog.getByRole('button', { name: 'Reopen inquiry' }).click()
  await expect(dialog.getByRole('status')).toContainText('Inquiry reopened.')
  expect(writes).toBe(3)
  await page.keyboard.press('Escape')
  await expect(page.getByRole('heading', { name: 'No matching inquiries' })).toBeVisible()
})

test('stale status displays a recoverable error without optimistic changes or retries', async ({ page }) => {
  let record = { ...original }
  let writes = 0
  await page.route(`**/api/v1/inquiries/${record.id}`, (route) => route.fulfill({ json: record }))
  await page.route(`**/api/v1/inquiries/${record.id}/status`, (route) => {
    writes++
    record = { ...record, status: 'resolved' }
    return route.fulfill({ status: 409, json: { detail: 'Status changed.' } })
  })
  await page.goto(`/inquiries?selected=${record.id}`)
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Start progress' }).click()
  await expect(dialog.getByRole('alert')).toContainText('Reload the inquiry')
  await expect(dialog.locator('.status-management .badge')).toHaveText('New')
  await expect(dialog.getByRole('button', { name: 'Start progress' })).toBeDisabled()
  await dialog.getByRole('button', { name: 'Reload inquiry' }).click()
  await expect(dialog.getByRole('button', { name: 'Reopen inquiry' })).toBeVisible()
  expect(writes).toBe(1)
})

test('unknown write outcome requires reload, not an automatic retry', async ({ page }) => {
  let writes = 0
  await page.route(`**/api/v1/inquiries/${original.id}`, (route) => route.fulfill({ json: original }))
  await page.route(`**/api/v1/inquiries/${original.id}/status`, (route) => {
    writes++
    return route.abort('failed')
  })
  await page.goto(`/inquiries?selected=${original.id}`)
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Start progress' }).click()
  await expect(dialog.getByRole('alert')).toContainText('could not be confirmed')
  await expect(dialog.locator('.status-management .badge')).toHaveText('New')
  expect(writes).toBe(1)
})

test('legacy insights and mobile keyboard controls remain accessible', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.route(`**/api/v1/inquiries/${original.id}`, (route) => route.fulfill({
    json: { ...original, category: null, ai_summary: null, priority: 'medium' },
  }))
  await page.goto(`/inquiries?selected=${original.id}`)
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByText('Unclassified / legacy-compatible')).toBeVisible()
  await expect(dialog.getByText(/Model, processing time, confidence, and source are not recorded/)).toBeVisible()
  await expect(dialog.getByRole('button', { name: 'Close inquiry details' })).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  const focusInside = await page.evaluate(() => document.querySelector('dialog')?.contains(document.activeElement))
  expect(focusInside).toBe(true)
  expect(await dialog.evaluate((element) => element.scrollWidth <= window.innerWidth)).toBe(true)
  await page.keyboard.press('Escape')
  await expect(dialog).not.toBeVisible()
  await page.getByRole('button', { name: 'Open navigation' }).click()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('button', { name: 'Open navigation' })).toBeFocused()
})
