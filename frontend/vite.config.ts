import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { defineConfig } from 'vite'

const tlsDir = process.env.INVOICEIQ_TEST_TLS_DIR
const https = tlsDir ? {
  key: readFileSync(join(tlsDir, 'key.pem')),
  cert: readFileSync(join(tlsDir, 'cert.pem')),
} : undefined

export default defineConfig({
  server: { host: '127.0.0.1', https, proxy: { '/api': 'http://127.0.0.1:8000' } },
  preview: { host: '127.0.0.1', proxy: { '/api': 'http://127.0.0.1:8000' } },
})
