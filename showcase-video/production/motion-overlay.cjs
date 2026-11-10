// Render React overlay artwork in Edge, with no network access or production changes.
const fs = require('node:fs/promises')
const path = require('node:path')
const React = require('../../frontend/node_modules/react')
const { renderToStaticMarkup } = require('../../frontend/node_modules/react-dom/server')
const { chromium } = require('../../frontend/node_modules/playwright')
const h = React.createElement
const scenes = require('./scenes.json')
const details = {
  dashboard: ['01', 'OVERVIEW', 'A fresh workspace'],
  upload: ['02', 'EXTRACTION', 'Juniper Studio · JS-1042'],
  review: ['03', 'HUMAN REVIEW', 'Verify and edit the fields'],
  save: ['04', 'PERSISTENCE', 'Saved and searchable'],
  analytics: ['05', 'ANALYTICS', 'USD 129.60 · recorded total'],
  duplicate: ['06', 'DUPLICATE CHECK', 'Vendor and invoice number match'],
}
const styles = 'html,body{margin:0;color:#f5fbfa;font-family:"Segoe UI",sans-serif}*{box-sizing:border-box}'

function Frame({ scene, step }) {
  const progress = Object.keys(details).map((key, index) =>
    h('span', { key, style: { width: 22, height: 5, background: index < +step ? '#57e7b5' : '#35535d', borderRadius: 5 } }))
  return h('main', { style: { position: 'absolute', inset: 0,
    background: 'radial-gradient(ellipse at 85% 12%,#174e4b 0%,transparent 42%),radial-gradient(ellipse at 4% 75%,#13374a 0%,transparent 46%),#091a27' } },
  h('header', { style: { position: 'absolute', left: 160, right: 160, top: 20, height: 56, display: 'flex', alignItems: 'center', gap: 15 } },
    h('div', { style: { width: 45, height: 45, background: '#9af2cd', borderRadius: 13, display: 'grid', placeItems: 'center', color: '#102b2d', fontSize: 21, fontWeight: 800 } }, 'IQ'),
    h('strong', { style: { fontSize: 25 } }, 'InvoiceIQ'),
    h('span', { style: { width: 1, height: 29, background: '#4b7276', margin: '0 15px' } }),
    h('strong', { style: { fontSize: 29, letterSpacing: '-.35px' } }, scene.title),
    h('div', { style: { marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 } },
      h('strong', { style: { color: '#b4f9de', fontSize: 15, letterSpacing: '2px', marginRight: 13 } }, 'LIVE DEMO · ' + step),
      ...progress)),
  h('div', { style: { position: 'absolute', left: 153, top: 81, width: 1614, height: 914, borderRadius: 14, border: '2px solid #76c5b4', background: '#23424b', boxShadow: '0 16px 48px #0009, 0 0 25px #54e4bb20' } }))
}

function Cue({ step, label, value }) {
  return h('aside', { style: { height: 76, margin: 5, width: 442, display: 'flex', alignItems: 'center', gap: 13,
    background: '#102b38', border: '1px solid #7be0bc', borderRadius: 15, boxShadow: '0 3px 10px #0006', padding: '10px 15px' } },
  h('span', { style: { flex: '0 0 36px', height: 36, display: 'grid', placeItems: 'center', color: '#102b2d',
    fontWeight: 800, fontSize: 16, borderRadius: 10, background: '#9af2cd' } }, step),
  h('div', null,
    h('div', { style: { fontSize: 13, color: '#aef2d7', fontWeight: 750, letterSpacing: '1.6px' } }, label),
    h('div', { style: { fontSize: 20, fontWeight: 650, marginTop: 3 } }, value)))
}

async function main() {
  const folder = path.join(__dirname, 'frames')
  await fs.mkdir(folder, { recursive: true })
  const browser = await chromium.launch({ channel: 'msedge' })
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } })
    for (const scene of scenes.filter(item => details[item.key])) {
      const [step, label, value] = details[scene.key]
      await page.setContent('<style>' + styles + '</style>' + renderToStaticMarkup(h(Frame, { scene, step })))
      await page.screenshot({ path: path.join(folder, scene.key + '-frame.png') })
      await page.setContent('<style>' + styles + '</style>' + renderToStaticMarkup(h(Cue, { step, label, value })))
      await page.screenshot({ path: path.join(folder, scene.key + '-cue.png'), omitBackground: true, clip: { x: 0, y: 0, width: 460, height: 90 } })
    }
  } finally {
    await browser.close()
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1 })
