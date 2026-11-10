FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    INVOICEIQ_PUBLIC_DEMO=1 TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/alembic.ini .
COPY backend/app app
COPY backend/migrations migrations
COPY sample-data/juniper-invoice.pdf /srv/sample-data/juniper-invoice.pdf

USER 10001:10001
EXPOSE 10000
CMD ["sh", "-c", "python -c 'import app.main' && python -m alembic upgrade head && exec python -m uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-10000}\" --workers 1 --limit-concurrency 24 --no-access-log"]
