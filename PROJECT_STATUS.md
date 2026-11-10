# InvoiceIQ status

The local MVP and the fictional public demo mode support upload, extraction, review, save, search, currency-separated analytics, duplicate detection, editing, deletion, and CSV export.

- **Public demo:** Signed 24-hour browser sessions scope every invoice operation. The public API accepts only the bundled fictional PDF, checks the frontend origin, and limits request size, duration, and rate.
- **Local regression:** Backend tests, the production frontend build, and both local and HTTPS browser workflows passed. CI exercises PostgreSQL migrations, API session isolation and both browser workflows, and builds and smoke-tests the Render image.
- **Deployment:** Vercel and Render configurations are prepared. The demo has not been published. Live provider configuration and an end-to-end hosted smoke test require explicit deployment authorization.
- **Showcase:** The README and LinkedIn script include the fictional Juniper Studio workflow.

Real invoice uploads remain a local feature. Hosted use with real financial records requires a separate production design.
