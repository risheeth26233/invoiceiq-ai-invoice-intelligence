# InvoiceIQ | Week 01 of 52

InvoiceIQ turns invoice documents into searchable records. The project pairs a React review interface with a FastAPI extraction service, an Alembic-managed database, and a dashboard that keeps monetary totals separate by currency.

Manual invoice entry is repetitive and prone to transcription errors. InvoiceIQ keeps a person in the loop by showing suggested values and requiring a save after review. Duplicate warnings use normalized vendor and invoice identifiers, or a matching vendor, date, currency, and amount.

## Demo script (45–60 seconds)

Open the [live demo](https://invoiceiq-demo-risheeth.vercel.app) in a fresh browser profile and select **Use sample invoice** to load the bundled Juniper Studio PDF. The repository includes the [review screenshot](screenshots/invoice-review.png) and [dashboard screenshot](screenshots/dashboard.png).

- **0–10s** Open the dashboard and explain the manual data-entry problem.
- **10–25s** Upload the fictional Juniper Studio invoice. Show invoice JS-1042 and confirm USD 129.60.
- **25–40s** Save the invoice, search for JS-1042, and open the USD breakdown in Analytics.
- **40–50s** Upload the same invoice again and show the reason for the duplicate warning.
- **50–60s** Point to the repository and explain why extraction drafts and saved records are separate.

Capture the invoice review screen, the duplicate warning, and the currency breakdown using synthetic data.

## LinkedIn draft

Week 01 of my 52 Weeks, 52 Projects challenge is InvoiceIQ, a tool for turning invoices into records you can review, search, and analyze.

I built it with React, TypeScript, FastAPI, and SQLAlchemy. One design decision mattered most: extraction creates a draft, and only a user-confirmed record affects the dashboard. I also kept spending totals separate by currency and made duplicate warnings explain which fields matched.

I deployed the fictional demo on Vercel, Render, and Neon. I verified the complete workflow in the hosted app, including that two separate browser profiles could only see their own records.

Try it: https://invoiceiq-demo-risheeth.vercel.app

Source: https://github.com/risheeth26233/invoiceiq-ai-invoice-intelligence

#BuildInPublic #52Weeks52Projects #React #FastAPI #DocumentProcessing
