import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

test('review, save, search, warn, edit, and delete', async ({ page }) => {
  const publicDemo = Boolean(process.env.INVOICEIQ_TEST_TLS_DIR)
  const sample = resolve('../sample-data/juniper-invoice.pdf')
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByText('Your workspace is ready')).toBeVisible()

  const upload = async (useSample = false) => {
    await page.getByRole('link', { name: 'Upload', exact: true }).click()
    if (publicDemo || useSample) await page.getByRole('button', { name: 'Use sample invoice' }).click()
    else await page.getByLabel('Choose an invoice').setInputFiles(sample)
    await expect(page.getByLabel('Vendor', { exact: true })).toHaveValue('Juniper Studio')
  }
  await upload(true)
  if (publicDemo) {
    await expect(page.getByLabel('Choose an invoice')).toHaveCount(0)
    expect(await page.context().cookies()).toContainEqual(expect.objectContaining({
      name: '__Host-invoiceiq', httpOnly: true, secure: true, sameSite: 'Strict',
    }))
  }
  if (process.env.INVOICEIQ_CAPTURE === '1') {
    await page.setViewportSize({ width: 1440, height: 960 })
    await page.screenshot({ path: '../screenshots/invoice-review.png', fullPage: true })
    await page.setViewportSize({ width: 390, height: 844 })
  }
  await page.getByLabel('Grand total').fill('130.25')
  await page.getByRole('button', { name: 'Save invoice' }).click()
  await expect(page.getByText('Invoice saved.')).toBeVisible()

  await page.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page.getByText('130.25', { exact: true })).toBeVisible()
  if (process.env.INVOICEIQ_CAPTURE === '1') {
    await page.setViewportSize({ width: 1440, height: 960 })
    await page.screenshot({ path: '../screenshots/dashboard.png', fullPage: true })
    await page.setViewportSize({ width: 390, height: 844 })
  }
  await upload()
  await page.getByRole('button', { name: 'Save invoice' }).click()
  await expect(page.getByText('Potential duplicates')).toBeVisible()
  await page.getByRole('button', { name: 'Cancel' }).click()
  await expect(page.getByText('Verify extracted fields')).toHaveCount(0)

  await page.getByRole('link', { name: 'Invoices', exact: true }).click()
  await page.getByRole('searchbox').fill('JS-1042')
  await page.getByRole('link', { name: 'Juniper Studio' }).click()
  await page.getByLabel('Vendor', { exact: true }).fill('Juniper Studio Updated')
  await page.getByLabel('Grand total').fill('131.25')
  await page.getByRole('button', { name: 'Save invoice' }).click()
  await expect(page.getByText('Invoice saved.')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Juniper Studio Updated' })).toBeVisible()
  await page.reload()
  await expect(page.getByLabel('Grand total')).toHaveValue('131.25')
  page.once('dialog', dialog => dialog.accept())
  await page.getByRole('button', { name: 'Delete invoice' }).click()
  await expect(page.getByText('No invoices to display.')).toBeVisible()
  await page.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page.getByText('Your workspace is ready')).toBeVisible()
})
