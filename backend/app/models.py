import os
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, create_engine, func
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(32), server_default="local", index=True)
    vendor: Mapped[str] = mapped_column(String(160), index=True)
    number: Mapped[str] = mapped_column(String(80))
    vendor_key: Mapped[str] = mapped_column(String(320), index=True)
    number_key: Mapped[str] = mapped_column(String(160), index=True)
    invoice_date: Mapped[date] = mapped_column(Date, index=True)
    due_date: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), index=True)
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    tax: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


url = os.environ.get("DATABASE_URL") or "sqlite:///./invoiceiq.db"
options = {"pool_size": 3, "max_overflow": 2} if url.startswith("postgresql") else {}
try:
    engine = create_engine(url, pool_pre_ping=True, hide_parameters=True, **options)
except (ArgumentError, ValueError):
    raise RuntimeError("DATABASE_URL is not a valid SQLAlchemy database URL.") from None
Session = sessionmaker(engine, expire_on_commit=False)
