"""store description

Revision ID: b8d1e2f3a4c5
Revises: a7c9d2e4f6b8
Create Date: 2026-06-25 17:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b8d1e2f3a4c5"
down_revision = "a7c9d2e4f6b8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("store_settings", sa.Column("store_description", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("store_settings", "store_description")