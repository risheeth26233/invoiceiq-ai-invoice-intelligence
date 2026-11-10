import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { api, type Analytics, type Page } from './api'
import { Details, Upload } from './Review'
import './style.css'

function useData<T>(path: string) {
  const [state, setState] = useState<{ data?: T; error?: string; path?: string }>({})
  useEffect(() => {
    let active = true
    api<T>(path).then(data => { if (active) setState({ data, path }) },
      error => { if (active) setState({ error: error.message, path }) })
    return () => { active = false }
  }, [path])
  return state.path === path ? state : {}
}

function InvoiceTable({ page }: { page: Page }) {
  if (!page.items.length) return <p className="muted">No invoices to display.</p>
  return <div className="scroll"><table>
    <thead><tr><th>Vendor</th><th>Invoice number</th><th>Issued</th><th>Total</th></tr></thead>
    <tbody>{page.items.map(invoice => <tr key={invoice.id}>
      <td><Link to={'/invoices/' + invoice.id}>{invoice.vendor}</Link></td>
      <td>{invoice.number}</td><td>{invoice.invoice_date}</td>
      <td className="amount">{invoice.currency} {invoice.total}</td>
    </tr>)}</tbody>
  </table></div>
}

function Dashboard({ expanded = false }: { expanded?: boolean }) {
  const { data, error } = useData<Analytics>('/analytics')
  const recent = useData<Page>('/invoices')
  return <>
    <header className="page-header">
      <div><p className="eyebrow">FINANCE WORKSPACE</p><h1>{expanded ? 'Spend analytics' : 'Overview'}</h1>
      <p className="muted intro">Track verified invoices and see where your money goes.</p></div>
      <Link className="button" to="/upload">+ Upload invoice</Link>
    </header>
    {error && <p className="error" role="alert">{error}</p>}
    {!data && !error && <p role="status">Loading totals…</p>}
    {data && <div className="metrics">
      <section className="card metric"><span>Saved invoices</span><strong>{data.count}</strong></section>
      {Object.entries(data.currencies).map(([code, group]) => <section className="card metric" key={code}>
        <span>{code} invoice value</span><strong>{group.total}</strong>
        <small>Recorded tax {group.tax_count ? group.tax : 'unavailable'} · {group.tax_count}/{group.count} invoices</small>
      </section>)}
    </div>}
    {data?.count === 0 && <section className="card empty">
      <h2>Your workspace is ready</h2><p>Upload an invoice and save the reviewed fields to populate your dashboard.</p>
      <Link to="/upload">Process your first invoice →</Link>
    </section>}
    {expanded && data && Object.entries(data.currencies).map(([code, group]) => <section className="card" key={code}>
      <h2>{code} breakdown</h2>
      <div className="form-grid">
        {([['Monthly trend', group.months], ['Vendor distribution', group.vendors]] as const).map(([title, amounts]) => {
          const points = Object.entries(amounts)
          const max = Math.max(1, ...points.map(([, value]) => Number(value)))
          return <div key={String(title)}><h3>{String(title)}</h3>
            {points.map(([name, value]) => <div className="bar" key={name}>
              <span>{name}</span><meter aria-label={name + ' ' + code} max={max} value={Number(value)} /><b>{value}</b>
            </div>)}
          </div>
        })}
      </div>
    </section>)}
    {!expanded && <section className="card">
      <h2>Recent invoices</h2>
      {recent.data ? <InvoiceTable page={{ ...recent.data, items: recent.data.items.slice(0, 5) }} /> :
        recent.error ? <p className="error" role="alert">{recent.error}</p> : <p role="status">Loading invoices…</p>}
    </section>}
  </>
}

function Invoices() {
  const [q, search] = useState('')
  const [currency, filter] = useState('')
  const [sort, order] = useState('newest')
  const [page, move] = useState(1)
  const currencies = useData<Analytics>('/analytics')
  const params = new URLSearchParams({ q, sort, page: String(page) })
  if (currency) params.set('currency', currency)
  const { data, error } = useData<Page>('/invoices?' + params)
  return <>
    <header className="page-header"><div><h1>All invoices</h1><p className="muted intro">Find and manage verified records.</p></div>
      <Link className="button" to="/upload">+ Upload invoice</Link></header>
    <section className="card">
      <p><a href="/api/invoices.csv">Export all invoices as CSV</a></p>
      <div className="filters">
        <label>Search<input type="search" value={q} maxLength={160} placeholder="Vendor or invoice number"
          onChange={event => { search(event.target.value); move(1) }} /></label>
        <label>Currency<select value={currency} onChange={event => { filter(event.target.value); move(1) }}>
          <option value="">All currencies</option>
          {Object.keys(currencies.data?.currencies ?? {}).map(code => <option key={code}>{code}</option>)}
        </select></label>
        <label>Sort<select value={sort} onChange={event => { order(event.target.value); move(1) }}>
          <option value="newest">Newest issued</option><option value="oldest">Oldest issued</option><option value="vendor">Vendor</option>
        </select></label>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {!data && !error && <p role="status">Loading invoices…</p>}
      {data && <><InvoiceTable page={data} /><div className="actions">
        <button className="secondary" disabled={page === 1} onClick={() => move(page - 1)}>Previous</button>
        <span>Page {page} · {data.total} records</span>
        <button className="secondary" disabled={page * 25 >= data.total} onClick={() => move(page + 1)}>Next</button>
      </div></>}
    </section>
  </>
}

function App() {
  const location = useLocation()
  return <div className="shell">
    <aside><Link className="brand" to="/"><span aria-hidden="true">IQ</span>InvoiceIQ</Link>
      <nav aria-label="Main navigation">
        <NavLink to="/" end>Overview</NavLink><NavLink to="/upload">Upload</NavLink>
        <NavLink to="/invoices">Invoices</NavLink><NavLink to="/analytics">Analytics</NavLink>
      </nav>
      <p className="aside-note">INVOICE INTELLIGENCE</p>
    </aside>
    <main>
      {location.state?.saved && <p role="status" className="success">Invoice saved.</p>}
      <Routes>
        <Route path="/" element={<Dashboard />} /><Route path="/upload" element={<Upload />} />
        <Route path="/invoices" element={<Invoices />} /><Route path="/invoices/:id" element={<Details />} />
        <Route path="/analytics" element={<Dashboard expanded />} />
        <Route path="*" element={<><h1>Page not found</h1><Link to="/">Return to overview</Link></>} />
      </Routes>
    </main>
  </div>
}

createRoot(document.getElementById('root')!).render(<BrowserRouter><App /></BrowserRouter>)
