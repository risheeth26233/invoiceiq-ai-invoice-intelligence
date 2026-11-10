import { execFileSync } from 'node:child_process'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

test('review, save, search, warn, edit, and delete', async ({ page }) => {
  const sample = resolve('../sample-data/juniper-invoice.pdf')
  const python = process.env.INVOICEIQ_PYTHON || 'python'
  execFileSync(python, [resolve('../sample-data/make_invoice.py')])
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByText('Your workspace is ready')).toBeVisible()

  const upload = async () => {
    await page.getByRole('link', { name: 'Upload', exact: true }).click()
    await page.getByLabel('Choose an invoice').setInputFiles(sample)
    await expect(page.getByLabel('Vendor', { exact: true })).toHaveValue('Juniper Studio')
  }
  await upload()
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
  await page.getByLabel('Grand total').fill('131.25')
  await page.getByRole('button', { name: 'Save invoice' }).click()
  await expect(page.getByText('Invoice saved.')).toBeVisible()
  await page.reload()
  await expect(page.getByLabel('Grand total')).toHaveValue('131.25')
  page.once('dialog', dialog => dialog.accept())
  await page.getByRole('button', { name: 'Delete invoice' }).click()
  await expect(page.getByText('No invoices to display.')).toBeVisible()
  await page.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page.getByText('Your workspace is ready')).toBeVisible()
})
