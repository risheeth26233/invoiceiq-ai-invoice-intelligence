# InvoiceIQ status

The local MVP is ready for the weekly portfolio showcase. It covers invoice upload, extraction, review, persistence, search, editing, duplicate warnings, deletion, CSV export, and currency-separated analytics.

- **Backend:** Eight local tests passed, including PNG, JPEG, and scanned PDF OCR, invalid uploads, and exact decimal totals across separate currencies.
- **Frontend:** Type checking and the production build passed. The Playwright workflow passed in Edge at a 390 px viewport, including an edit that refreshes the invoice heading.
- **Database:** The local SQLite migration and schema check passed. GitHub Actions runs the browser workflow against a disposable PostgreSQL 16 service.
- **Showcase:** The README contains the fictional invoice demo and screenshots. The LinkedIn draft includes a 45–60 second walkthrough.
- **Deployment:** Local only. Public hosting requires authentication, tenant isolation, rate limits, and isolation of untrusted document processing.

Line-item extraction, advanced insights, and broader invoice-layout coverage are deferred.
