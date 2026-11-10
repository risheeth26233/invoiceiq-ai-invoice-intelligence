import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { api, extract, fields, json, type Extraction, type Fields, type Invoice } from './api'

import { useData } from './useData'

function Review({ initial, id, confidence, cancel }: {
  initial: Fields; id?: number; confidence?: Extraction['confidence']; cancel?: () => void
}) {
  const [values, setValues] = useState(initial)
  const [matches, setMatches] = useState<{ id: number; reason: string }[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (matches.length === 0) {
        const duplicates = await api<typeof matches>('/invoices/duplicates' + (id ? '?exclude=' + id : ''), json('POST', values))
        if (duplicates.length) {
          setMatches(duplicates)
          return
        }
      }
      const record = await api<Invoice>(id ? '/invoices/' + id : '/invoices', json(id ? 'PUT' : 'POST', values))
      navigate('/invoices/' + record.id, { replace: true, state: { saved: true } })
    } catch (issue) {
      setError((issue as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    if (!window.confirm('Permanently delete this invoice?')) return
    setBusy(true)
    try {
      await api('/invoices/' + id, { method: 'DELETE' })
      navigate('/invoices', { replace: true })
    } catch (issue) {
      setError((issue as Error).message)
      setBusy(false)
    }
  }

  return <form className="card" onSubmit={save}>
    <h2>{id ? 'Invoice details' : 'Verify extracted fields'}</h2>
    <p className="muted">Check the values against the original before saving.</p>
    <div className="form-grid">
      {fields.map(([key, label, type]) => <label key={key}>
        {label}
        {confidence?.[key] && confidence[key] !== 'matched' &&
          <small>{confidence[key] === 'missing' ? ' · Missing' : ' · Review OCR'}</small>}
        <input disabled={busy} type={type} value={values[key] ?? ''} step={type === 'number' ? '0.01' : undefined}
          min={type === 'number' ? 0 : undefined} pattern={key === 'currency' ? '[A-Za-z]{3}' : undefined}
          maxLength={key === 'currency' ? 3 : key === 'vendor' ? 160 : key === 'number' ? 80 : undefined}
          required={['vendor', 'number', 'invoice_date', 'currency', 'total'].includes(key)}
          onChange={event => { setValues({ ...values, [key]: event.target.value || null }); setMatches([]) }} />
      </label>)}
    </div>
    {matches.length > 0 && <div className="notice" role="alert">
      <strong>Potential duplicates</strong>
      <ul>{matches.map(match => <li key={match.id}>
        <Link to={'/invoices/' + match.id}>Record #{match.id}</Link> · {match.reason}
      </li>)}</ul>
    </div>}
    {error && <p className="error" role="alert">{error}</p>}
    <div className="actions">
      <button disabled={busy}>{busy ? 'Working…' : matches.length ? 'Save anyway' : 'Save invoice'}</button>
      {cancel && <button type="button" className="secondary" onClick={cancel} disabled={busy}>Cancel</button>}
      {id && <button type="button" className="danger" onClick={remove} disabled={busy}>Delete invoice</button>}
    </div>
  </form>
}

export function Upload() {
  const [preview, setPreview] = useState<{ url: string; file: File }>()
  const [result, setResult] = useState<Extraction>()
  const [progress, setProgress] = useState<number>()
  const [error, setError] = useState('')

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview.url) }, [preview])

  async function select(file?: File) {
    if (!file || progress !== undefined) return
    setError('')
    if (!/\.(pdf|png|jpe?g)$/i.test(file.name) || file.size > 10 * 1024 * 1024) {
      setError('Choose a PDF, PNG, or JPEG file up to 10 MiB.')
      return
    }
    setResult(undefined)
    setPreview({ url: URL.createObjectURL(file), file })
    setProgress(0)
    try {
      setResult(await extract(file, setProgress))
    } catch (issue) {
      setError((issue as Error).message)
    } finally {
      setProgress(undefined)
    }
  }

  return <>
    <h1>Upload invoice</h1>
    <p className="muted intro">Turn a document into a record you can review, search, and track.</p>
    <div className="card drop" onDragOver={event => event.preventDefault()}
      onDrop={event => { event.preventDefault(); void select(event.dataTransfer.files[0]) }}>
      <h2>Drop an invoice here</h2>
      <p className="muted">PDF, PNG or JPEG · up to 10 MiB</p>
      <input aria-label="Choose an invoice" type="file" accept=".pdf,.png,.jpg,.jpeg"
        disabled={progress !== undefined} onChange={event => {
          const file = event.target.files?.[0]
          event.target.value = ''
          void select(file)
        }} />
      {progress !== undefined && <p role="status">
        {progress === 100 ? 'Extracting invoice fields…' : 'Uploading…'}
        {' '}<progress aria-label="Upload progress" max={100} value={progress} />
      </p>}
      {error && <p className="error" role="alert">{error}</p>}
    </div>
    <div className="review-grid">
      {preview && (progress !== undefined || result) && <section className="card preview">
        <h2>Source document</h2>
        <p className="muted filename">{preview.file.name}</p>
        {/\.pdf$/i.test(preview.file.name)
          ? <a href={preview.url} target="_blank" rel="noreferrer">Open PDF preview</a>
          : <img src={preview.url} alt="Uploaded invoice" />}
        {result?.warnings.map(message => <p className="notice" key={message}>{message}</p>)}
      </section>}
      {result && <Review initial={result.fields} confidence={result.confidence}
        cancel={() => { setPreview(undefined); setResult(undefined) }} />}
    </div>
  </>
}

export function Details() {
  const { id } = useParams()
  const { data: invoice, error } = useData<Invoice>('/invoices/' + id)
  return <>
    <Link to="/invoices">← All invoices</Link>
    <h1>{invoice ? invoice.vendor : 'Invoice record'}</h1>
    {error && <p role="alert" className="error">{error}</p>}
    {!error && !invoice && <p role="status">Loading invoice…</p>}
    {invoice && <Review key={invoice.id} id={invoice.id} initial={invoice} />}
  </>
}
