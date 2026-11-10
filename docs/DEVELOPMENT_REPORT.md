# Development report

InvoiceIQ uses React and TypeScript for the review interface, FastAPI for the local API, SQLAlchemy and Alembic for persistence, and PyMuPDF for PDF text extraction and Tesseract OCR. The upload endpoint bounds the streamed body and checks the file signature before processing. The browser keeps the preview locally and the database stores confirmed fields.

## Engineering decisions

- Extraction returns a draft with missing or OCR-derived fields marked for review. It never creates an invoice record.
- Search escapes wildcard characters. Duplicate warnings compare normalized vendor and invoice identifiers and can also use date, currency, and total.
- Money uses decimal values and aggregates are separated by currency. SQLite is the local fallback. PostgreSQL still needs live verification.
- OCR is optional and uses locally installed English language data. Rules currently target labelled invoices and English OCR.
- The project uses the PyMuPDF 1.26.7 wheel after pip rejected a newer Windows download on an integrity mismatch.

## Remaining work

Check extraction across diverse layouts, implement line-item capture and insights, prepare screenshots and cloud configuration, and add authentication and document processing isolation before public hosting.

## Portfolio release

Dashboard and detail views share one data-loading hook. Create and update share the same invoice field mapping, the frontend uses React Router directly, and image OCR opens the converted PDF without copying its pages. Regression checks cover blank labels, compact values, normalized duplicate keys after edits, exact currency totals, and vendor heading updates. The local workflow uses SQLite, and the GitHub Actions browser workflow is configured to use a disposable PostgreSQL 16 database.
