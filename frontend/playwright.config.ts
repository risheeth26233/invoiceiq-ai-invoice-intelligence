import { defineConfig } from '@playwright/test'

const python = process.env.INVOICEIQ_PYTHON || 'python'

export default defineConfig({
  testDir: './tests',
  use: { baseURL: 'http://127.0.0.1:5173', channel: process.env.PLAYWRIGHT_CHANNEL },
  webServer: [
    {
      command: 'npm run dev -- --strictPort',
      url: 'http://127.0.0.1:5173',
    },
    {
      command: `"${python}" -m alembic upgrade head && "${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: '../backend',
      env: { DATABASE_URL: process.env.INVOICEIQ_BROWSER_DATABASE_URL || 'sqlite:///./browser-test.db' },
      url: 'http://127.0.0.1:8000/api/health',
    },
  ],
})
