"""expenses

Revision ID: e4b9a1c6d2f3
Revises: d2a7c9e8f1b4
Create Date: 2026-07-27 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "e4b9a1c6d2f3"
down_revision = "d2a7c9e8f1b4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "expense",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expense_date", "expense", ["expense_date"])
    op.create_index("ix_expense_category", "expense", ["category"])


def downgrade():
    op.drop_index("ix_expense_category", table_name="expense")
    op.drop_index("ix_expense_date", table_name="expense")
    op.drop_table("expense")