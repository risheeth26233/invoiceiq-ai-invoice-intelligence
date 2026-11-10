import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  use: { baseURL: 'http://127.0.0.1:5173', channel: process.env.PLAYWRIGHT_CHANNEL },
  webServer: [
    {
      command: 'npm run dev -- --strictPort',
      url: 'http://127.0.0.1:5173',
    },
    {
      command: `${process.env.INVOICEIQ_PYTHON || 'python'} -m alembic upgrade head && ${process.env.INVOICEIQ_PYTHON || 'python'} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: '../backend',
      env: { DATABASE_URL: 'sqlite:///./browser-test.db' },
      url: 'http://127.0.0.1:8000/api/health',
    },
  ],
})
