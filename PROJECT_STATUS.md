# InvoiceIQ status

The local MVP and the fictional public demo mode support upload, extraction, review, save, search, currency-separated analytics, duplicate detection, editing, deletion, and CSV export.

- **Public demo:** Signed 24-hour browser sessions scope every invoice operation. The public API accepts only the bundled fictional PDF, checks the frontend origin, and limits request size, duration, and rate.
- **Local regression:** Backend tests, the production frontend build, and both local and HTTPS browser workflows passed. CI exercises PostgreSQL migrations, API session isolation and both browser workflows, and builds and smoke-tests the Render image.
- **Deployment:** The [live demo](https://invoiceiq-demo-risheeth.vercel.app) runs on Vercel Hobby, Render Free, and Neon Free. The direct Render health endpoint returned HTTP 200.
- **Hosted verification:** The fictional invoice extracted and saved, appeared in search, contributed USD 129.60 to analytics, and triggered a duplicate warning. A separate browser profile saw an empty workspace and received HTTP 404 for the first profile's invoice. A direct Neon query confirmed the fictional record and migration `0002`.
- **Showcase:** The README and LinkedIn script include the fictional Juniper Studio workflow.

Real invoice uploads remain a local feature. Hosted use with real financial records requires a separate production design.
