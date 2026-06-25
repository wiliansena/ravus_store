"""store settings

Revision ID: f4d2e7c10a15
Revises: c31f1a26d4e9
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f4d2e7c10a15"
down_revision = "c31f1a26d4e9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "store_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("store_name", sa.String(length=120), nullable=False),
        sa.Column("whatsapp_number", sa.String(length=30), nullable=True),
        sa.Column("logo_filename", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "INSERT INTO store_settings (store_name, whatsapp_number, logo_filename) "
        "VALUES ('Ravus Store', '5599999999999', '')"
    )


def downgrade():
    op.drop_table("store_settings")
