import csv
from decimal import Decimal
from io import StringIO

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from starlette.concurrency import run_in_threadpool
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session as DBSession

from .extraction import MAX_BYTES, read_document
from .models import Invoice, Session
from .schemas import InvoiceInput, InvoiceRecord

app = FastAPI(title="InvoiceIQ", version="0.1.0")


def database():
    with Session() as session:
        yield session


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/extract")
async def extract(request: Request):
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, "The maximum file size is 10 MiB.")
        data.extend(chunk)
    try:
        return await run_in_threadpool(read_document, bytes(data))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def normalize(value):
    return "".join(character for character in value.casefold() if character.isalnum())


def invoice_or_404(session, invoice_id):
    record = session.get(Invoice, invoice_id)
    if record is None:
        raise HTTPException(404, "Invoice not found.")
    return record


@app.post("/api/invoices/duplicates")
def duplicates(data: InvoiceInput, exclude: int | None = None, session: DBSession = Depends(database)):
    vendor, number = normalize(data.vendor), normalize(data.number)
    exact = and_(Invoice.number_key == number, Invoice.number_key != "")
    same_amount = and_(Invoice.invoice_date == data.invoice_date, Invoice.total == data.total,
                       Invoice.currency == data.currency)
    query = select(Invoice).where(Invoice.vendor_key == vendor, Invoice.vendor_key != "", or_(exact, same_amount))
    if exclude is not None:
        query = query.where(Invoice.id != exclude)
    return [{"id": row.id, "reason": "Same vendor and invoice number" if row.number_key == number and number
             else "Same vendor, invoice date, currency and total"} for row in session.scalars(query.limit(10))]


@app.post("/api/invoices", response_model=InvoiceRecord, status_code=201)
def create(data: InvoiceInput, session: DBSession = Depends(database)):
    record = Invoice(**data.model_dump(), vendor_key=normalize(data.vendor), number_key=normalize(data.number))
    session.add(record)
    session.commit()
    return record


@app.get("/api/invoices")
def listing(q: str = Query("", max_length=160), currency: str | None = Query(None, pattern=r"^[A-Z]{3}$"),
            sort: str = Query("newest", pattern=r"^(newest|oldest|vendor)$"),
            page: int = Query(1, ge=1, le=10000), session: DBSession = Depends(database)):
    query = select(Invoice)
    if q.strip():
        query = query.where(or_(Invoice.vendor.icontains(q.strip(), autoescape=True),
                                Invoice.number.icontains(q.strip(), autoescape=True)))
    if currency:
        query = query.where(Invoice.currency == currency)
    order = {"newest": Invoice.invoice_date.desc(), "oldest": Invoice.invoice_date, "vendor": Invoice.vendor}[sort]
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    items = session.scalars(query.order_by(order, Invoice.id.desc()).offset((page - 1) * 25).limit(25))
    return {"items": [InvoiceRecord.model_validate(row).model_dump(mode="json") for row in items], "total": total}


@app.get("/api/invoices.csv")
def export(session: DBSession = Depends(database)):
    output = StringIO()
    writer = csv.writer(output)
    columns = tuple(InvoiceRecord.model_fields)
    writer.writerow(columns)
    for record in session.scalars(select(Invoice).order_by(Invoice.id)):
        values = InvoiceRecord.model_validate(record).model_dump(mode="json")
        # Escape formula prefixes in user-supplied spreadsheet cells.
        for key in ("vendor", "number"):
            if values[key].lstrip().startswith(("=", "+", "-", "@")):
                values[key] = "'" + values[key]
        writer.writerow(values[key] for key in columns)
    return Response(output.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="invoices.csv"'})


@app.get("/api/invoices/{invoice_id}", response_model=InvoiceRecord)
def detail(invoice_id: int, session: DBSession = Depends(database)):
    return invoice_or_404(session, invoice_id)


@app.put("/api/invoices/{invoice_id}", response_model=InvoiceRecord)
def update(invoice_id: int, data: InvoiceInput, session: DBSession = Depends(database)):
    record = invoice_or_404(session, invoice_id)
    for key, value in data.model_dump().items():
        setattr(record, key, value)
    record.vendor_key = normalize(data.vendor)
    record.number_key = normalize(data.number)
    session.commit()
    return record


@app.delete("/api/invoices/{invoice_id}", status_code=204)
def delete(invoice_id: int, session: DBSession = Depends(database)):
    session.delete(invoice_or_404(session, invoice_id))
    session.commit()


@app.get("/api/analytics")
def analytics(session: DBSession = Depends(database)):
    # ponytail: aggregate in Python for exact SQLite decimals. Move grouped sums to PostgreSQL for larger datasets.
    currencies = {}
    for currency, total, tax, invoice_date, vendor in session.execute(
        select(Invoice.currency, Invoice.total, Invoice.tax, Invoice.invoice_date, Invoice.vendor)
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
