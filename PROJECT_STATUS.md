# InvoiceIQ status

The first local MVP covers upload, extraction, manual review, persistence, search, editing, duplicate warnings, deletion, CSV export, and currency-separated analytics.

- **Backend:** Seven tests passed, including PNG, JPEG, and scanned PDF OCR and invalid upload handling.
- **Frontend:** Type checking and the production build passed. One Playwright workflow passed in Edge at a 390 px viewport.
- **Database:** SQLite migration and schema check passed. PostgreSQL SQL generation passed and a live database test is pending.
- **Deployment:** Local development only. Public hosting requires authentication, tenant isolation, rate limits, and isolation of untrusted document processing.

Portfolio work still includes sample layout coverage, line items, insights, hosting configuration, and showcase screenshots.
