"""cash adjustments

Revision ID: f8a2c7d9e1b5
Revises: e4b9a1c6d2f3
Create Date: 2026-09-05 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "f8a2c7d9e1b5"
down_revision = "e4b9a1c6d2f3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cash_adjustment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("adjustment_date", sa.Date(), nullable=False),
        sa.Column("movement_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cash_adjustment_date", "cash_adjustment", ["adjustment_date"])
    op.create_index("ix_cash_adjustment_type", "cash_adjustment", ["movement_type"])


def downgrade():
    op.drop_index("ix_cash_adjustment_type", table_name="cash_adjustment")
    op.drop_index("ix_cash_adjustment_date", table_name="cash_adjustment")
    op.drop_table("cash_adjustment")