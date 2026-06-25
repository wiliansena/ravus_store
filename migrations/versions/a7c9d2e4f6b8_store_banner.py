"""store banner

Revision ID: a7c9d2e4f6b8
Revises: f4d2e7c10a15
Create Date: 2026-06-25 17:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a7c9d2e4f6b8"
down_revision = "f4d2e7c10a15"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("store_settings", sa.Column("banner_filename", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("store_settings", "banner_filename")