import csv
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import StringIO
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from sqlalchemy import and_, delete as delete_rows, func, or_, select
from sqlalchemy.orm import Session as DBSession

from .extraction import MAX_BYTES, read_document
from .models import Invoice, Session
from .schemas import InvoiceInput, InvoiceRecord
from .security import COOKIE, SESSION_SECONDS, Demo, DemoSecurity, demo_from_env

router = APIRouter()
SAMPLE = (Path(__file__).resolve().parents[2] / "sample-data/juniper-invoice.pdf").read_bytes()
demo_save_lock = Lock()


def invoice_owner(request: Request):
    return request.state.invoice_owner if request.app.state.demo else "local"


Owner = Annotated[str, Depends(invoice_owner)]


def owned(owner, *columns):
    return select(*(columns or (Invoice,))).where(Invoice.owner == owner)


def database():
    with Session() as session:
        yield session


@router.get("/api/health")
def health():
    return {"status": "ok"}


@router.post("/api/session")
def start_session(request: Request, response: Response):
    demo = request.app.state.demo
    if demo and not request.state.invoice_owner:
        response.set_cookie(COOKIE, demo.issue(), max_age=SESSION_SECONDS, secure=True,
                            httponly=True, samesite="strict", path="/")
    return {"public_demo": demo is not None}


@router.get("/api/sample")
def sample():
    return Response(SAMPLE, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="juniper-invoice.pdf"'})


@router.post("/api/extract")
async def extract(request: Request):
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, "The maximum file size is 10 MiB.")
        data.extend(chunk)
    demo = request.app.state.demo
    if demo and data != demo.sample:
        raise HTTPException(422, "The public demo accepts only the bundled fictional invoice.")
    try:
        return await run_in_threadpool(read_document, bytes(data))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def normalize(value):
    return "".join(character for character in value.casefold() if character.isalnum())


def invoice_values(data: InvoiceInput):
    return data.model_dump() | {
        "vendor_key": normalize(data.vendor),
        "number_key": normalize(data.number),
    }


def invoice_or_404(session, owner, invoice_id):
    record = session.scalar(owned(owner).where(Invoice.id == invoice_id))
    if record is None:
        raise HTTPException(404, "Invoice not found.")
    return record


@router.post("/api/invoices/duplicates")
def duplicates(data: InvoiceInput, owner: Owner, exclude: int | None = None, session: DBSession = Depends(database)):
    vendor, number = normalize(data.vendor), normalize(data.number)
    exact = and_(Invoice.number_key == number, Invoice.number_key != "")
    same_amount = and_(Invoice.invoice_date == data.invoice_date, Invoice.total == data.total,
                       Invoice.currency == data.currency)
    query = owned(owner).where(Invoice.vendor_key == vendor, Invoice.vendor_key != "", or_(exact, same_amount))
    if exclude is not None:
        query = query.where(Invoice.id != exclude)
    return [{"id": row.id, "reason": "Same vendor and invoice number" if row.number_key == number and number
             else "Same vendor, invoice date, currency and total"} for row in session.scalars(query.limit(10))]


@router.post("/api/invoices", response_model=InvoiceRecord, status_code=201)
def create(data: InvoiceInput, owner: Owner, request: Request, session: DBSession = Depends(database)):
    record = Invoice(owner=owner, **invoice_values(data))
    demo = request.app.state.demo
    # The single demo worker serializes the quota check and insert.
    with demo_save_lock if demo else nullcontext():
        if demo:
            cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=SESSION_SECONDS)
            session.execute(delete_rows(Invoice).where(Invoice.owner != "local", Invoice.created_at < cutoff))
            if session.scalar(select(func.count()).select_from(owned(owner).subquery())) >= 25:
                raise HTTPException(409, "This demo session already has 25 invoices. Delete one before saving.")
        session.add(record)
        session.commit()
    return record


@router.get("/api/invoices")
def listing(owner: Owner, q: str = Query("", max_length=160), currency: str | None = Query(None, pattern=r"^[A-Z]{3}$"),
            sort: str = Query("newest", pattern=r"^(newest|oldest|vendor)$"),
            page: int = Query(1, ge=1, le=10000), session: DBSession = Depends(database)):
    query = owned(owner)
    if q.strip():
        query = query.where(or_(Invoice.vendor.icontains(q.strip(), autoescape=True),
                                Invoice.number.icontains(q.strip(), autoescape=True)))
    if currency:
        query = query.where(Invoice.currency == currency)
    order = {"newest": Invoice.invoice_date.desc(), "oldest": Invoice.invoice_date, "vendor": Invoice.vendor}[sort]
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    items = session.scalars(query.order_by(order, Invoice.id.desc()).offset((page - 1) * 25).limit(25))
    return {"items": [InvoiceRecord.model_validate(row).model_dump(mode="json") for row in items], "total": total}


@router.get("/api/invoices.csv")
def export(owner: Owner, session: DBSession = Depends(database)):
    output = StringIO()
    writer = csv.writer(output)
    columns = tuple(InvoiceRecord.model_fields)
    writer.writerow(columns)
    for record in session.scalars(owned(owner).order_by(Invoice.id)):
        values = InvoiceRecord.model_validate(record).model_dump(mode="json")
        # Escape formula prefixes in user-supplied spreadsheet cells.
        for key in ("vendor", "number"):
            if values[key].lstrip().startswith(("=", "+", "-", "@")):
                values[key] = "'" + values[key]
        writer.writerow(values[key] for key in columns)
    return Response(output.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="invoices.csv"'})


@router.get("/api/invoices/{invoice_id}", response_model=InvoiceRecord)
def detail(invoice_id: int, owner: Owner, session: DBSession = Depends(database)):
    return invoice_or_404(session, owner, invoice_id)


@router.put("/api/invoices/{invoice_id}", response_model=InvoiceRecord)
def update(invoice_id: int, data: InvoiceInput, owner: Owner, session: DBSession = Depends(database)):
    record = invoice_or_404(session, owner, invoice_id)
    for key, value in invoice_values(data).items():
        setattr(record, key, value)
    session.commit()
    return record


@router.delete("/api/invoices/{invoice_id}", status_code=204)
def delete(invoice_id: int, owner: Owner, session: DBSession = Depends(database)):
    session.delete(invoice_or_404(session, owner, invoice_id))
    session.commit()


@router.get("/api/analytics")
def analytics(owner: Owner, session: DBSession = Depends(database)):
    # ponytail: aggregate in Python for exact SQLite decimals. Move grouped sums to PostgreSQL for larger datasets.
    currencies = {}
    for currency, total, tax, invoice_date, vendor in session.execute(
        owned(owner, Invoice.currency, Invoice.total, Invoice.tax, Invoice.invoice_date, Invoice.vendor)
    ):
        group = currencies.setdefault(currency, {"count": 0, "total": Decimal(0), "tax": Decimal(0),
                                                 "tax_count": 0, "months": {}, "vendors": {}})
        group["count"] += 1
        group["total"] += total
        if tax is not None:
            group["tax"] += tax
            group["tax_count"] += 1
        month = invoice_date.strftime("%Y-%m")
        group["months"][month] = group["months"].get(month, Decimal(0)) + total
        group["vendors"][vendor] = group["vendors"].get(vendor, Decimal(0)) + total
    return {"count": sum(group["count"] for group in currencies.values()), "currencies": {
        code: {**group, "total": str(group["total"]), "tax": str(group["tax"]),
               "months": {key: str(value) for key, value in sorted(group["months"].items())},
               "vendors": {key: str(value) for key, value in sorted(group["vendors"].items(), key=lambda item: -item[1])}}
        for code, group in sorted(currencies.items())
    }}


def create_app(demo: Demo | None = None):
    app = FastAPI(title="InvoiceIQ", version="0.2.0",
                  docs_url=None if demo else "/docs", redoc_url=None if demo else "/redoc",
                  openapi_url=None if demo else "/openapi.json")
    app.state.demo = demo
    app.include_router(router)
    if demo:
        app.add_middleware(DemoSecurity, demo=demo)
        app.add_middleware(CORSMiddleware, allow_origins=[demo.origin], allow_credentials=True,
                           allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])
    return app


app = create_app(demo_from_env(SAMPLE))
