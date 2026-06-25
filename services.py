import os
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db
from forms import ProductForm
from models import Brand, Category, Client, Color, Permission, ProductImage, ProductVariant, Role, Size, StoreSettings, Supplier, User
from utils_uploads import salvar_upload_produto


def money(value):
    value = Decimal(value or 0)
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_decimal_br(value):
    if value is None:
        return Decimal("0")
    text = str(value).strip().replace("R$", "").replace(" ", "")
    if not text:
        return Decimal("0")

    comma_pos = text.rfind(",")
    dot_pos = text.rfind(".")
    if comma_pos > -1 and dot_pos > -1:
        if comma_pos > dot_pos:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma_pos > -1:
        text = text.replace(".", "").replace(",", ".")

    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValueError("Valor monetario invalido.")


def decimal_to_br(value):
    value = Decimal(value or 0)
    return f"{value:.2f}".replace(".", ",")


def get_store_settings():
    settings = StoreSettings.query.first()
    if settings:
        return settings
    settings = StoreSettings(store_name="Ravus Store", whatsapp_number=Config.WHATSAPP_NUMBER)
    db.session.add(settings)
    db.session.commit()
    return settings


def registry_map():
    return {
        "categorias": {
            "model": Category,
            "title": "Categorias",
            "singular": "categoria",
            "placeholder": "Ex: Camisetas, Calcas, Vestidos",
        },
        "marcas": {
            "model": Brand,
            "title": "Marcas",
            "singular": "marca",
            "placeholder": "Ex: Ravus, Nike, Adidas",
        },
        "cores": {
            "model": Color,
            "title": "Cores",
            "singular": "cor",
            "placeholder": "Ex: Preto, Branco, Azul",
        },
        "tamanhos": {
            "model": Size,
            "title": "Tamanhos",
            "singular": "tamanho",
            "placeholder": "Ex: P, M, G, 38, 40",
        },
        "fornecedores": {
            "model": Supplier,
            "title": "Fornecedores",
            "singular": "fornecedor",
            "placeholder": "Ex: Fornecedor Atacado SP",
        },
        "clientes": {
            "model": Client,
            "title": "Clientes",
            "singular": "cliente",
            "placeholder": "Ex: Maria Silva",
        },
    }


def permission_required(permission_name):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped_view(*args, **kwargs):
            if not current_user.has_permission(permission_name):
                flash("Voce nao tem permissao para acessar essa area.")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def save_product_images(product, files, primary_upload_index=0):
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    next_position = len(product.images)
    saved_count = 0
    has_primary = any(image.is_primary for image in product.images)
    try:
        primary_upload_index = int(primary_upload_index or 0)
    except (TypeError, ValueError):
        primary_upload_index = 0
    for upload_index, file in enumerate(files):
        if not file or not file.filename:
            continue
        filename = salvar_upload_produto(file)
        if not filename:
            flash(f"Imagem ignorada: {file.filename}")
            continue
        is_primary = not has_primary and saved_count == 0
        if upload_index == primary_upload_index:
            is_primary = True
        if is_primary:
            for image in product.images:
                image.is_primary = False
            has_primary = True
        db.session.add(ProductImage(product=product, filename=filename, position=next_position, is_primary=is_primary))
        next_position += 1
        saved_count += 1
    return saved_count


def product_form_context(product=None):
    categories = Category.query.order_by(Category.name).all()
    brands = Brand.query.order_by(Brand.name).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    colors = Color.query.order_by(Color.name).all()
    sizes = Size.query.order_by(Size.name).all()
    form = ProductForm(obj=product)
    form.set_choices(categories, brands, suppliers, colors, sizes)
    if product and not form.is_submitted():
        form.preco_venda.data = decimal_to_br(product.preco_venda)
        form.category_id.data = product.category_id or 0
        form.brand_id.data = product.brand_id or 0
        form.supplier_id.data = product.supplier_id or 0
        form.active.data = product.active
    return {
        "product": product,
        "form": form,
        "categories": categories,
        "brands": brands,
        "colors": colors,
        "sizes": sizes,
        "suppliers": suppliers,
    }


def custo_medio_variant(variant):
    entradas = [
        movement
        for movement in variant.stock_movements
        if movement.quantity > 0 and movement.preco_custo is not None
    ]
    total_quantidade = sum(movement.quantity for movement in entradas)
    if total_quantidade <= 0:
        return Decimal("0")
    total_custo = sum(movement.preco_custo * movement.quantity for movement in entradas)
    return total_custo / total_quantidade


def seed_data():
    for model, names in [
        (Category, ["Camisetas", "Calcas", "Vestidos", "Acessorios"]),
        (Brand, ["Ravus"]),
        (Color, ["Preto", "Branco", "Azul", "Vermelho"]),
        (Size, ["PP", "P", "M", "G", "GG"]),
    ]:
        for name in names:
            if not model.query.filter_by(name=name).first():
                db.session.add(model(name=name))

    permission_data = [
        ("produtos", "Cadastrar e consultar produtos"),
        ("estoque", "Movimentar e ajustar estoque"),
        ("vendas", "Registrar vendas e emitir recibos"),
        ("relatorios", "Consultar relatorios"),
        ("usuarios", "Gerenciar usuarios e permissoes"),
    ]
    for name, description in permission_data:
        if not Permission.query.filter_by(name=name).first():
            db.session.add(Permission(name=name, description=description))
    db.session.commit()

    if not Role.query.filter_by(name="Administrador").first():
        role = Role(name="Administrador", permissions=Permission.query.all())
        db.session.add(role)
        db.session.commit()

    admin_role = Role.query.filter_by(name="Administrador").first()
    admin_email = Config.ADMIN_EMAIL.strip().lower()
    if not User.query.filter_by(email=admin_email).first():
        db.session.add(
            User(
                name=Config.ADMIN_NAME,
                email=admin_email,
                password_hash=generate_password_hash(Config.ADMIN_PASSWORD),
                active=True,
                role=admin_role,
            )
        )
        db.session.commit()
