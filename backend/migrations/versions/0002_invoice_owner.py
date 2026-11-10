from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"


def upgrade():
    op.add_column("invoices", sa.Column("owner", sa.String(32), server_default="local", nullable=False))
    op.create_index("ix_invoices_owner", "invoices", ["owner"])


def downgrade():
    op.drop_index("ix_invoices_owner", table_name="invoices")
    op.drop_column("invoices", "owner")
