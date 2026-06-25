"""product description

Revision ID: c31f1a26d4e9
Revises: 8f2b8d45a1c7
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c31f1a26d4e9"
down_revision = "8f2b8d45a1c7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("product", sa.Column("descricao", sa.Text(), nullable=True))
    op.execute("UPDATE product SET descricao = '' WHERE descricao IS NULL")


def downgrade():
    op.drop_column("product", "descricao")
