from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None


def upgrade():
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor", sa.String(160), nullable=False),
        sa.Column("number", sa.String(80), nullable=False),
        sa.Column("vendor_key", sa.String(320), nullable=False),
        sa.Column("number_key", sa.String(160), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date()),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 2)),
        sa.Column("tax", sa.Numeric(14, 2)),
        sa.Column("total", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for name in ("vendor", "vendor_key", "number_key", "invoice_date", "currency"):
        op.create_index(f"ix_invoices_{name}", "invoices", [name])


def downgrade():
    op.drop_table("invoices")
