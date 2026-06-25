"""product featured flag

Revision ID: c9e1f2a3b4d6
Revises: b8d1e2f3a4c5
Create Date: 2026-06-25 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "c9e1f2a3b4d6"
down_revision = "b8d1e2f3a4c5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "product",
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_product_active_featured", "product", ["active", "featured"])
    op.alter_column("product", "featured", server_default=None)


def downgrade():
    op.drop_index("ix_product_active_featured", table_name="product")
    op.drop_column("product", "featured")