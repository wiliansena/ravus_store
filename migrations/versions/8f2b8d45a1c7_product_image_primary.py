"""product image primary

Revision ID: 8f2b8d45a1c7
Revises: 5b0f56319dbd
Create Date: 2026-06-20 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "8f2b8d45a1c7"
down_revision = "5b0f56319dbd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("product_image", sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()))
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE product_image pi
            SET is_primary = true
            WHERE pi.id IN (
                SELECT DISTINCT ON (product_id) id
                FROM product_image
                ORDER BY product_id, position, id
            )
            """
        )
    )
    op.alter_column("product_image", "is_primary", server_default=None)


def downgrade():
    op.drop_column("product_image", "is_primary")
