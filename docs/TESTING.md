# Testing

From `backend`, run `python -m alembic upgrade head`, `python -m alembic check`, and `python -m pytest -q` using the project virtual environment. Set `TESSDATA_PREFIX` to a directory containing `eng.traineddata` to include PNG, JPEG, and scanned PDF tests.

From `frontend`, run `npm ci` and `npm run build`. For the browser workflow, set `INVOICEIQ_PYTHON` to the absolute backend virtual environment executable path, install Chromium with `npx playwright install chromium`, then run `npx playwright test`. Use `PLAYWRIGHT_CHANNEL=msedge` to test with an existing Edge installation. Ports 5173 and 8000 must be available for the test servers. The browser test uses a separate local SQLite database by default. To exercise PostgreSQL, set `INVOICEIQ_BROWSER_DATABASE_URL` to a disposable, empty test database. The GitHub Actions workflow provisions one for its browser run.

Set `INVOICEIQ_CAPTURE=1` to regenerate the portfolio screenshots from synthetic data.
