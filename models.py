import os
from decimal import Decimal

from flask import url_for

from config import Config
from datetime_utils import now_brazil
from extensions import db


role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permission.id"), primary_key=True),
)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)


class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)


class Color(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)


class Size(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), default="")


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), default="")


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.String(160), default="")


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    permissions = db.relationship("Permission", secondary=role_permissions, backref="roles")


class User(db.Model):
    __tablename__ = "app_user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    role = db.relationship("Role")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return self.active

    def get_id(self):
        return str(self.id)

    def has_permission(self, permission_name):
        if not self.role:
            return False
        return any(permission.name == permission_name for permission in self.role.permissions)


class StoreSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(120), nullable=False, default="Ravus Store")
    whatsapp_number = db.Column(db.String(30), default="")
    logo_filename = db.Column(db.String(255), default="")

    @property
    def logo_url(self):
        if not self.logo_filename:
            return ""
        return url_for("static", filename=f"uploads/store/{self.logo_filename}")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    sku = db.Column(db.String(60), unique=True)
    descricao = db.Column(db.Text, default="")
    preco_venda = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    image_url = db.Column(db.String(400), default="")
    active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    brand_id = db.Column(db.Integer, db.ForeignKey("brand.id"))
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"))
    category = db.relationship("Category")
    brand = db.relationship("Brand")
    supplier = db.relationship("Supplier")
    variants = db.relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images = db.relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.position",
    )

    @property
    def ordered_images(self):
        return sorted(self.images, key=lambda image: (not image.is_primary, image.position, image.id))

    @property
    def primary_image(self):
        return next((image for image in self.ordered_images if image.is_primary), self.ordered_images[0] if self.ordered_images else None)

    @property
    def catalog_images(self):
        uploaded_images = [image.file_url for image in self.ordered_images]
        if uploaded_images:
            return uploaded_images
        if self.image_url:
            return [self.image_url]
        return []


class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now_brazil)
    product = db.relationship("Product", back_populates="images")

    @property
    def file_url(self):
        return url_for("static", filename=f"uploads/products/{self.filename}")

    @property
    def thumb_url(self):
        stem = os.path.splitext(self.filename)[0]
        thumb_filename = f"{stem}.webp"
        thumb_path = os.path.join(Config.PRODUCT_THUMB_FOLDER, thumb_filename)
        if os.path.exists(thumb_path):
            return url_for("static", filename=f"uploads/products/thumbs/{thumb_filename}")
        return self.file_url

class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey("color.id"))
    size_id = db.Column(db.Integer, db.ForeignKey("size.id"))
    min_stock = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship("Product", back_populates="variants")
    color = db.relationship("Color")
    size = db.relationship("Size")
    stock_movements = db.relationship("StockMovement", back_populates="variant")

    @property
    def label(self):
        parts = [self.product.name]
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.name)
        return " / ".join(parts)

    @property
    def stock(self):
        total = sum(m.quantity for m in self.stock_movements)
        sold = sum(item.quantity for item in self.sale_items)
        return total - sold


class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variant.id"), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    preco_custo = db.Column(db.Numeric(10, 2), nullable=True)
    note = db.Column(db.String(200), default="")
    created_at = db.Column(db.DateTime, nullable=False, default=now_brazil)
    variant = db.relationship("ProductVariant", back_populates="stock_movements")


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"))
    discount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    payment_method = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now_brazil)
    client = db.relationship("Client")
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    @property
    def subtotal(self):
        return sum(item.total for item in self.items)

    @property
    def total(self):
        return max(Decimal("0"), self.subtotal - self.discount)


class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sale.id"), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variant.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    preco_venda_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    preco_custo_unitario = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    sale = db.relationship("Sale", back_populates="items")
    variant = db.relationship("ProductVariant", backref="sale_items")

    @property
    def total(self):
        return self.preco_venda_unitario * self.quantity

    @property
    def custo_total(self):
        return self.preco_custo_unitario * self.quantity

    @property
    def lucro_total(self):
        return self.total - self.custo_total
