# Deployment preparation

The frontend builds to `frontend/dist`. A static host should route browser navigation to `index.html` and proxy `/api/*` to the FastAPI service on the same origin. The backend entry point is `app.main:app`, run from `backend`. Configure the platform's listening port and check `/api/health`.

Provide a PostgreSQL DSN through the `DATABASE_URL` environment variable using SQLAlchemy's `postgresql+psycopg` driver. Run `python -m alembic upgrade head` as a single release step before serving traffic. PostgreSQL migration SQL was generated locally. Validate it against the target PostgreSQL instance before deployment.

Before hosting real invoice data, require authenticated requests, scope every invoice operation to its owner or tenant, isolate document processing, and configure rate limits, storage and backup policies, and HTTPS. Keep environment secrets in the host's secret store. For a demo, use only fictional invoices.
