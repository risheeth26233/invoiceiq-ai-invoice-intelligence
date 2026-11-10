# API reference

FastAPI exposes interactive documentation at http://127.0.0.1:8000/docs. Endpoints use the `/api` prefix.

| Method and path | Purpose |
| --- | --- |
| POST /session | Return the mode and start a signed browser session in public demo mode |
| GET /sample | Download the bundled fictional PDF |
| GET /health | Check that the API is responding |
| POST /extract | Upload raw PDF, PNG, or JPEG bytes and receive editable draft fields |
| GET /invoices | List records with optional `q`, `currency`, `sort`, and `page` |
| POST /invoices/duplicates | Preview potential duplicates with optional `exclude` record ID |
| POST /invoices | Save a verified record |
| GET, PUT, DELETE /invoices/{id} | Read, replace, or delete a record |
| GET /invoices.csv | Export saved invoices |
| GET /analytics | Return counts and per-currency values, recorded tax, months, and vendors |

Money values are decimal strings in responses. Uploads larger than 10 MiB return HTTP 413. Unreadable files and invalid fields return HTTP 422. Extraction does not persist a draft.

In public demo mode, invoice and extraction endpoints require a signed session cookie. Writes require the configured frontend origin. The demo accepts only the exact sample bytes and returns HTTP 429 on rate limits. The 10 MiB limit applies to local uploads.
