"""Add SKU, unit price and reorder level to products.

Revision ID: 0002_add_sku_price_reorder
Revises: 0001_create_products
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_sku_price_reorder"
down_revision = "0001_create_products"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("products", sa.Column("sku", sa.String(length=40), nullable=True))
    # Backfill existing rows so the NOT NULL + UNIQUE constraints can be applied.
    op.execute("UPDATE products SET sku = 'SKU-' || id WHERE sku IS NULL")
    op.alter_column("products", "sku", nullable=False)
    op.create_unique_constraint("uq_products_sku", "products", ["sku"])
    op.add_column(
        "products",
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="10"),
    )
    op.add_column(
        "products",
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("products", "unit_price")
    op.drop_column("products", "reorder_level")
    op.drop_constraint("uq_products_sku", "products", type_="unique")
    op.drop_column("products", "sku")
