"""sale cancel status

Revision ID: d2a7c9e8f1b4
Revises: c9e1f2a3b4d6
Create Date: 2026-06-30 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "d2a7c9e8f1b4"
down_revision = "c9e1f2a3b4d6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sale", sa.Column("status", sa.String(length=20), nullable=False, server_default="ativa"))
    op.add_column("sale", sa.Column("canceled_at", sa.DateTime(), nullable=True))
    op.add_column("sale", sa.Column("cancel_reason", sa.String(length=300), nullable=True))
    op.add_column("sale", sa.Column("canceled_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_sale_canceled_by_id_app_user", "sale", "app_user", ["canceled_by_id"], ["id"])
    op.create_index("ix_sale_status_created_at", "sale", ["status", "created_at"])
    op.alter_column("sale", "status", server_default=None)


def downgrade():
    op.drop_index("ix_sale_status_created_at", table_name="sale")
    op.drop_constraint("fk_sale_canceled_by_id_app_user", "sale", type_="foreignkey")
    op.drop_column("sale", "canceled_by_id")
    op.drop_column("sale", "cancel_reason")
    op.drop_column("sale", "canceled_at")
    op.drop_column("sale", "status")