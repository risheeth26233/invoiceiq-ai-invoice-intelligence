import { defineConfig } from '@playwright/test'

const python = process.env.INVOICEIQ_PYTHON || 'python'
const demo = Boolean(process.env.INVOICEIQ_TEST_TLS_DIR)
const baseURL = demo ? 'https://127.0.0.1:5173' : 'http://127.0.0.1:5173'
const app = demo ? '--app-dir tests serve_demo:app' : 'app.main:app'

export default defineConfig({
  testDir: './tests',
  use: { baseURL, ignoreHTTPSErrors: demo, channel: process.env.PLAYWRIGHT_CHANNEL },
  webServer: [
    {
      command: 'npm run dev -- --strictPort',
      url: baseURL,
      ignoreHTTPSErrors: demo,
    },
    {
      command: `"${python}" -m alembic upgrade head && "${python}" -m uvicorn ${app} --host 127.0.0.1 --port 8000`,
      cwd: '../backend',
      env: { DATABASE_URL: process.env.INVOICEIQ_BROWSER_DATABASE_URL || 'sqlite:///./browser-test.db' },
      url: 'http://127.0.0.1:8000/api/health',
    },
  ],
})
