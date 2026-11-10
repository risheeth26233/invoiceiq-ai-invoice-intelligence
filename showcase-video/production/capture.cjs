const assert = require('node:assert/strict')
const fs = require('node:fs/promises')
const path = require('node:path')
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '../../frontend/node_modules/playwright')
const origin = 'https://invoiceiq-demo-risheeth.vercel.app'
const folder = path.join(__dirname, 'captures')
const marks = {}
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))

async function main() {
  await fs.mkdir(folder, { recursive: true })
  const browser = await chromium.launch({ channel: 'msedge', headless: true })
  const context = await browser.newContext({
    baseURL: origin, viewport: { width: 1440, height: 810 },
    recordVideo: { dir: folder, size: { width: 1440, height: 810 } },
  })
  await context.addInitScript(() => {
    window.addEventListener('DOMContentLoaded', () => {
      const dot = document.createElement('div')
      dot.style.cssText = 'position:fixed;width:24px;height:24px;border:3px solid #15b88b;border-radius:50%;box-shadow:0 0 0 3px #ffffffb0;pointer-events:none;z-index:99999;opacity:0;transform:translate(-50%,-50%);transition:background .18s,opacity .2s'
      document.body.append(dot)
      window.addEventListener('mousemove', e => {
        dot.style.left = e.clientX + 'px'
        dot.style.top = e.clientY + 'px'
        dot.style.opacity = '1'
      })
      window.addEventListener('mousedown', () => {
        dot.style.background = '#15b88b88'
        setTimeout(() => { dot.style.background = 'transparent' }, 230)
      })
    })
  })
  const zero = Date.now()
  const page = await context.newPage()
  const video = page.video()
  let invoicePath
  const now = () => (Date.now() - zero) / 1000
  const beat = async (key, duration, actions) => {
    const start = now()
    await actions()
    await sleep(Math.max(850, (start + duration - now()) * 1000))
    marks[key] = [start, now()]
    console.log(key, marks[key].map(x => x.toFixed(2)).join('–'))
  }
  const link = name => page.getByRole('link', { name, exact: true })
  async function click(locator, hold = 180) {
    await locator.hover()
    await sleep(hold)
    await locator.click()
  }
  const total = page.getByLabel('Grand total')
  const sample = page.getByRole('button', { name: 'Use sample invoice' })
  const save = () => page.getByRole('button', { name: 'Save invoice' })
  try {
    await page.goto('/')
    await page.getByText('Your workspace is ready').waitFor({ timeout: 100000 })
    await beat('dashboard', 7, async () => {
      await sleep(2200)
      await page.getByRole('heading', { name: 'Overview' }).hover()
    })
    await beat('upload', 10, async () => {
      await click(link('Upload'))
      await sleep(1150)
      await click(sample)
      await page.getByLabel('Invoice number').waitFor()
      assert.equal(await page.getByLabel('Invoice number').inputValue(), 'JS-1042')
      await sleep(950)
      await total.scrollIntoViewIfNeeded()
      await total.hover()
    })
    await beat('review', 8, async () => {
      await sleep(1300)
      await click(total)
      await total.fill('129.00')
      await sleep(1050)
      await total.fill('129.60')
      await sleep(1350)
      await save().hover()
    })
    await beat('save', 10, async () => {
      await sleep(600)
      await click(save())
      await page.getByText('Invoice saved.').waitFor()
      invoicePath = new URL(page.url()).pathname.replace('/invoices/', '/api/invoices/')
      assert.match(invoicePath, /^\/api\/invoices\/\d+$/)
      await sleep(1900)
      await click(link('Invoices'))
      const search = page.getByRole('searchbox')
      await click(search)
      await search.pressSequentially('JS-1042', { delay: 125 })
      await page.getByRole('link', { name: 'Juniper Studio' }).waitFor()
      await sleep(1200)
      await click(page.getByRole('link', { name: 'Juniper Studio' }))
    })
    await beat('analytics', 8, async () => {
      await click(link('Analytics'))
      await page.getByText('USD invoice value').waitFor()
      await page.locator('.metric').getByText('129.60', { exact: true }).waitFor()
      await sleep(1200)
      await page.locator('.metric').getByText('129.60', { exact: true }).hover()
    })
    await beat('duplicate', 9, async () => {
      await click(link('Upload'))
      await sleep(500)
      await click(sample)
      await save().waitFor()
      await sleep(750)
      await click(save())
      const warning = page.getByText('Same vendor and invoice number')
      await warning.waitFor()
      await warning.scrollIntoViewIfNeeded()
      await warning.hover()
    })
    await page.close()
    await video.saveAs(path.join(folder, 'live.webm'))
    await fs.writeFile(path.join(folder, 'marks.json'), JSON.stringify(marks, null, 2))
  } finally {
    try {
      if (invoicePath) {
        const response = await context.request.delete(invoicePath, { headers: { Origin: origin } })
        assert.equal(response.status(), 204)
      }
    } finally {
      await context.close()
      await browser.close()
    }
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1 })
