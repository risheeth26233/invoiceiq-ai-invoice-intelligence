export const fields = [
  ['vendor', 'Vendor', 'text'], ['number', 'Invoice number', 'text'],
  ['invoice_date', 'Invoice date', 'date'], ['due_date', 'Due date', 'date'],
  ['currency', 'Currency', 'text'], ['subtotal', 'Subtotal', 'number'],
  ['tax', 'Tax', 'number'], ['total', 'Grand total', 'number'],
] as const

export type Fields = Record<typeof fields[number][0], string | null>
export type Invoice = Fields & { id: number }
export type Extraction = { fields: Fields; confidence: Partial<Record<keyof Fields, string>>; warnings: string[] }
export type Page = { items: Invoice[]; total: number }
export type Analytics = {
  count: number
  currencies: Record<string, {
    count: number; total: string; tax: string; tax_count: number
    months: Record<string, string>; vendors: Record<string, string>
  }>
}

async function readError(response: Response) {
  const error = await response.json().catch(() => ({}))
  return new Error(typeof error.detail === 'string' ? error.detail : 'The request failed. Try again.')
}

let session: Promise<{ public_demo: boolean }> | undefined

export function startSession() {
  session ??= fetch('/api/session', { method: 'POST' }).then(async response => {
    if (!response.ok) throw await readError(response)
    return response.json()
  }).catch(error => {
    session = undefined
    throw error
  })
  return session
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const current = startSession()
  await current
  let response = await fetch('/api' + path, init)
  if (response.status === 401) {
    if (session === current) session = undefined
    await startSession()
    response = await fetch('/api' + path, init)
  }
  if (!response.ok) throw await readError(response)
  return response.status === 204 ? undefined as T : response.json()
}

export async function sampleInvoice() {
  const response = await fetch('/api/sample')
  if (!response.ok) throw await readError(response)
  return new File([await response.blob()], 'juniper-invoice.pdf', { type: 'application/pdf' })
}

export function json(method: string, values: Fields): RequestInit {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) }
}

async function sendUpload(file: File, progress: (value: number) => void): Promise<Extraction | undefined> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', '/api/extract')
    request.responseType = 'json'
    request.timeout = 120_000
    request.upload.onprogress = event => {
      if (event.lengthComputable) progress(Math.round(100 * event.loaded / event.total))
    }
    request.upload.onload = () => progress(100)
    request.onload = () => {
      if (request.status === 401) resolve(undefined)
      else if (request.status === 200 && request.response) resolve(request.response)
      else reject(new Error(request.response?.detail || 'The document could not be processed.'))
    }
    request.onerror = () => reject(new Error('Could not connect to InvoiceIQ.'))
    request.ontimeout = () => reject(new Error('Document processing timed out.'))
    request.setRequestHeader('Content-Type', 'application/octet-stream')
    request.send(file)
  })
}

export async function extract(file: File, progress: (value: number) => void) {
  const current = startSession()
  await current
  const result = await sendUpload(file, progress)
  if (result) return result
  if (session === current) session = undefined
  await startSession()
  const retry = await sendUpload(file, progress)
  if (!retry) throw new Error('The demo session could not start. Check that cookies are enabled.')
  return retry
}
