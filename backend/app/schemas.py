from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]


class InvoiceInput(BaseModel):
    vendor: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    number: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    invoice_date: date
    due_date: date | None = None
    currency: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{3}$")]
    subtotal: Money | None = None
    tax: Money | None = None
    total: Money


class InvoiceRecord(InvoiceInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
