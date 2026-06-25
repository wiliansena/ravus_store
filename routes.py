import os
from datetime import datetime
from urllib.parse import quote_plus

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from datetime_utils import today_brazil
from extensions import db
from models import (
    Brand,
    Category,
    Client,
    Color,
    Permission,
    Product,
    ProductImage,
    ProductVariant,
    Role,
    Sale,
    SaleItem,
    Size,
    StoreSettings,
    StockMovement,
    Supplier,
    User,
)
from services import (
    custo_medio_variant,
    get_store_settings,
    parse_decimal_br,
    permission_required,
    product_form_context,
    registry_map,
    save_product_images,
    seed_data,
)
from utils_uploads import copiar_imagem_produto, salvar_upload_banner, salvar_upload_logo


def register_routes(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form["email"].strip().lower()
            user = User.query.filter_by(email=email).first()
            if not user or not user.active or not check_password_hash(user.password_hash, request.form["password"]):
                flash("E-mail ou senha invalidos.", "error")
                return redirect(url_for("login"))
            login_user(user)
            return redirect(request.args.get("next") or url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Sessao encerrada.")
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def dashboard():
        today = today_brazil()
        month_sales = Sale.query.filter(func.date(Sale.created_at) >= today.replace(day=1)).all()
        low_stock = [v for v in ProductVariant.query.all() if v.stock <= v.min_stock]
        return render_template(
            "dashboard.html",
            product_count=Product.query.count(),
            stock_total=sum(v.stock for v in ProductVariant.query.all()),
            sales_total=sum(s.total for s in month_sales),
            low_stock=low_stock,
        )

    @app.route("/configuracoes", methods=["GET", "POST"])
    @permission_required("usuarios")
    def store_settings():
        settings = get_store_settings()
        if request.method == "POST":
            settings.store_name = request.form["store_name"].strip() or "Ravus Store"
            settings.whatsapp_number = request.form.get("whatsapp_number", "").strip()
            settings.store_description = request.form.get("store_description", "").strip()
            logo = salvar_upload_logo(request.files.get("logo"))
            if logo:
                if settings.logo_filename:
                    old_path = os.path.join(Config.LOGO_UPLOAD_FOLDER, settings.logo_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                settings.logo_filename = logo
            banner = salvar_upload_banner(request.files.get("banner"))
            if banner:
                if settings.banner_filename:
                    old_path = os.path.join(Config.LOGO_UPLOAD_FOLDER, settings.banner_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                settings.banner_filename = banner
            db.session.commit()
            flash("Configuracoes atualizadas.")
            return redirect(url_for("store_settings"))
        return render_template("store_settings.html", settings=settings)

    @app.route("/cadastros/<kind>")
    @login_required
    def simple_registry(kind):
        registries = registry_map()
        if kind not in registries:
            abort(404)
        meta = registries[kind]
        model = meta["model"]
        page = request.args.get("page", 1, type=int)
        pagination = model.query.order_by(model.name).paginate(page=page, per_page=10, error_out=False)
        return render_template(
            "registry.html",
            kind=kind,
            meta=meta,
            registries=registries,
            pagination=pagination,
            items=pagination.items,
        )

    @app.route("/cadastros/<kind>/novo", methods=["GET", "POST"])
    @login_required
    def new_registry_item(kind):
        registries = registry_map()
        if kind not in registries:
            abort(404)
        meta = registries[kind]
        model = meta["model"]
        if request.method == "POST":
            item = model(name=request.form["name"].strip())
            if hasattr(item, "phone"):
                item.phone = request.form.get("phone", "").strip()
            db.session.add(item)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(f"Ja existe {meta['singular']} com esse nome.", "error")
                return redirect(url_for("new_registry_item", kind=kind))
            flash(f"{meta['singular'].capitalize()} salvo.")
            return redirect(url_for("simple_registry", kind=kind))
        return render_template("registry_form.html", kind=kind, meta=meta, item=None)

    @app.route("/cadastros/<kind>/<int:item_id>/editar", methods=["GET", "POST"])
    @login_required
    def edit_registry_item(kind, item_id):
        registries = registry_map()
        if kind not in registries:
            abort(404)
        meta = registries[kind]
        model = meta["model"]
        item = db.get_or_404(model, item_id)
        if request.method == "POST":
            item.name = request.form["name"].strip()
            if hasattr(item, "phone"):
                item.phone = request.form.get("phone", "").strip()
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(f"Ja existe {meta['singular']} com esse nome.", "error")
                return redirect(url_for("edit_registry_item", kind=kind, item_id=item.id))
            flash(f"{meta['singular'].capitalize()} atualizado.")
            return redirect(url_for("simple_registry", kind=kind))
        return render_template("registry_form.html", kind=kind, meta=meta, item=item)

    @app.route("/cadastros/<kind>/<int:item_id>/excluir", methods=["POST"])
    @login_required
    def delete_registry_item(kind, item_id):
        registries = registry_map()
        if kind not in registries:
            abort(404)
        meta = registries[kind]
        model = meta["model"]
        item = db.get_or_404(model, item_id)
        try:
            db.session.delete(item)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"Nao foi possivel excluir: {meta['singular']} possui vinculos no sistema.", "error")
            return redirect(url_for("simple_registry", kind=kind))
        flash(f"{meta['singular'].capitalize()} excluido.")
        return redirect(url_for("simple_registry", kind=kind))

    @app.route("/usuarios", methods=["GET", "POST"])
    @permission_required("usuarios")
    def users():
        page = request.args.get("page", 1, type=int)
        pagination = User.query.order_by(User.name).paginate(page=page, per_page=10, error_out=False)
        return render_template("users.html", users=pagination.items, pagination=pagination)

    @app.route("/usuarios/novo", methods=["GET", "POST"])
    @permission_required("usuarios")
    def new_user():
        if request.method == "POST":
            email = request.form["email"].strip().lower()
            if User.query.filter_by(email=email).first():
                flash("Ja existe um usuario com esse e-mail.", "error")
                return redirect(url_for("new_user"))
            user = User(
                name=request.form["name"].strip(),
                email=email,
                password_hash=generate_password_hash(request.form["password"]),
                role_id=request.form.get("role_id") or None,
                active=bool(request.form.get("active")),
            )
            db.session.add(user)
            db.session.commit()
            flash("Usuario salvo.")
            return redirect(url_for("users"))
        return render_template("user_form.html", user=None, roles=Role.query.order_by(Role.name).all())

    @app.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
    @permission_required("usuarios")
    def edit_user(user_id):
        user = db.get_or_404(User, user_id)
        if request.method == "POST":
            email = request.form["email"].strip().lower()
            existing_user = User.query.filter(User.email == email, User.id != user.id).first()
            if existing_user:
                flash("Ja existe outro usuario com esse e-mail.", "error")
                return redirect(url_for("edit_user", user_id=user.id))
            user.name = request.form["name"].strip()
            user.email = email
            user.role_id = request.form.get("role_id") or None
            user.active = bool(request.form.get("active"))
            if user.id == current_user.id:
                user.active = True
            db.session.commit()
            flash("Usuario atualizado.")
            return redirect(url_for("users"))
        return render_template("user_form.html", user=user, roles=Role.query.order_by(Role.name).all())

    @app.route("/usuarios/<int:user_id>/resetar-senha", methods=["POST"])
    @permission_required("usuarios")
    def reset_user_password(user_id):
        user = db.get_or_404(User, user_id)
        new_password = request.form["new_password"].strip()
        if len(new_password) < 6:
            flash("A nova senha precisa ter pelo menos 6 caracteres.", "error")
            return redirect(url_for("edit_user", user_id=user.id))
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash(f"Senha de {user.name} redefinida.")
        return redirect(url_for("edit_user", user_id=user.id))

    @app.route("/usuarios/<int:user_id>/excluir", methods=["POST"])
    @permission_required("usuarios")
    def delete_user(user_id):
        user = db.get_or_404(User, user_id)
        if user.id == current_user.id:
            flash("Voce nao pode excluir o usuario que esta usando agora.", "warning")
            return redirect(url_for("users"))
        try:
            db.session.delete(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Nao foi possivel excluir: usuario possui vinculos no sistema.", "error")
            return redirect(url_for("users"))
        flash("Usuario excluido.")
        return redirect(url_for("users"))

    @app.route("/perfis")
    @permission_required("usuarios")
    def roles():
        page = request.args.get("page", 1, type=int)
        pagination = Role.query.order_by(Role.name).paginate(page=page, per_page=10, error_out=False)
        return render_template("roles.html", roles=pagination.items, pagination=pagination)

    @app.route("/perfis/novo", methods=["GET", "POST"])
    @permission_required("usuarios")
    def new_role():
        if request.method == "POST":
            permission_ids = [int(value) for value in request.form.getlist("permission_ids")]
            role = Role(name=request.form["name"].strip())
            role.permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
            db.session.add(role)
            db.session.commit()
            flash("Perfil de acesso salvo.")
            return redirect(url_for("roles"))
        return render_template("role_form.html", role=None, permissions=Permission.query.order_by(Permission.name).all())

    @app.route("/perfis/<int:role_id>/editar", methods=["GET", "POST"])
    @permission_required("usuarios")
    def edit_role(role_id):
        role = db.get_or_404(Role, role_id)
        if request.method == "POST":
            role.name = request.form["name"].strip()
            permission_ids = [int(value) for value in request.form.getlist("permission_ids")]
            role.permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
            db.session.commit()
            flash("Perfil atualizado.")
            return redirect(url_for("roles"))
        return render_template("role_form.html", role=role, permissions=Permission.query.order_by(Permission.name).all())

    @app.route("/perfis/<int:role_id>/excluir", methods=["POST"])
    @permission_required("usuarios")
    def delete_role(role_id):
        role = db.get_or_404(Role, role_id)
        try:
            db.session.delete(role)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Nao foi possivel excluir: perfil possui usuarios vinculados.", "error")
            return redirect(url_for("roles"))
        flash("Perfil excluido.")
        return redirect(url_for("roles"))

    @app.route("/permissoes")
    @permission_required("usuarios")
    def permissions():
        page = request.args.get("page", 1, type=int)
        pagination = Permission.query.order_by(Permission.name).paginate(page=page, per_page=10, error_out=False)
        return render_template("permissions.html", permissions=pagination.items, pagination=pagination)

    @app.route("/permissoes/nova", methods=["GET", "POST"])
    @permission_required("usuarios")
    def new_permission():
        if request.method == "POST":
            db.session.add(Permission(name=request.form["name"].strip(), description=request.form.get("description", "").strip()))
            db.session.commit()
            flash("Permissao salva.")
            return redirect(url_for("permissions"))
        return render_template("permission_form.html", permission=None)

    @app.route("/permissoes/<int:permission_id>/editar", methods=["GET", "POST"])
    @permission_required("usuarios")
    def edit_permission(permission_id):
        permission = db.get_or_404(Permission, permission_id)
        if request.method == "POST":
            permission.name = request.form["name"].strip()
            permission.description = request.form.get("description", "").strip()
            db.session.commit()
            flash("Permissao atualizada.")
            return redirect(url_for("permissions"))
        return render_template("permission_form.html", permission=permission)

    @app.route("/permissoes/<int:permission_id>/excluir", methods=["POST"])
    @permission_required("usuarios")
    def delete_permission(permission_id):
        permission = db.get_or_404(Permission, permission_id)
        try:
            db.session.delete(permission)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Nao foi possivel excluir: permissao possui perfis vinculados.", "error")
            return redirect(url_for("permissions"))
        flash("Permissao excluida.")
        return redirect(url_for("permissions"))

    @app.route("/produtos")
    @permission_required("produtos")
    def products():
        page = request.args.get("page", 1, type=int)
        search = request.args.get("q", "").strip()
        query = Product.query
        if search:
            term = f"%{search}%"
            query = query.filter(Product.name.ilike(term))
        pagination = query.order_by(Product.name).paginate(page=page, per_page=10, error_out=False)
        return render_template("products.html", products=pagination.items, pagination=pagination, search=search)

    @app.route("/produtos/novo", methods=["GET", "POST"])
    @permission_required("produtos")
    def new_product():
        context = product_form_context()
        form = context["form"]
        if form.validate_on_submit():
            product = Product(
                name=form.name.data.strip(),
                sku=form.sku.data or None,
                descricao=(form.descricao.data or "").strip(),
                preco_venda=parse_decimal_br(form.preco_venda.data),
                image_url="",
                category_id=form.category_id.data or None,
                brand_id=form.brand_id.data or None,
                supplier_id=form.supplier_id.data or None,
                active=True,
                featured=form.featured.data,
            )
            db.session.add(product)
            db.session.flush()
            variant = ProductVariant(
                product_id=product.id,
                color_id=form.color_id.data or None,
                size_id=form.size_id.data or None,
                min_stock=int(form.min_stock.data or 1),
            )
            db.session.add(variant)
            save_product_images(product, request.files.getlist("images"), request.form.get("primary_upload_index"))
            db.session.commit()
            flash("Produto cadastrado.")
            return redirect(url_for("products"))
        return render_template("product_form.html", **context)

    @app.route("/produtos/<int:product_id>/editar", methods=["GET", "POST"])
    @permission_required("produtos")
    def edit_product(product_id):
        product = db.get_or_404(Product, product_id)
        context = product_form_context(product)
        form = context["form"]
        if form.validate_on_submit():
            sku = form.sku.data or None
            existing_product = Product.query.filter(Product.sku == sku, Product.id != product.id).first() if sku else None
            if existing_product:
                flash("Ja existe outro produto com esse SKU.", "error")
                return redirect(url_for("edit_product", product_id=product.id))
            product.name = form.name.data.strip()
            product.sku = sku
            product.descricao = (form.descricao.data or "").strip()
            product.preco_venda = parse_decimal_br(form.preco_venda.data)
            product.active = form.active.data
            product.featured = form.featured.data
            product.category_id = form.category_id.data or None
            product.brand_id = form.brand_id.data or None
            product.supplier_id = form.supplier_id.data or None
            save_product_images(product, request.files.getlist("images"), request.form.get("primary_upload_index"))
            db.session.commit()
            flash("Produto atualizado.")
            return redirect(url_for("products"))
        return render_template("product_form.html", **context)

    @app.route("/produtos/<int:product_id>/copiar", methods=["POST"])
    @permission_required("produtos")
    def duplicate_product(product_id):
        product = db.get_or_404(Product, product_id)
        base_name = f"{product.name} - copia"
        copy_name = base_name
        counter = 2
        while Product.query.filter_by(name=copy_name).first():
            copy_name = f"{base_name} {counter}"
            counter += 1

        duplicated = Product(
            name=copy_name,
            sku=None,
            descricao=product.descricao,
            preco_venda=product.preco_venda,
            image_url=product.image_url,
            active=False,
            featured=False,
            category_id=product.category_id,
            brand_id=product.brand_id,
            supplier_id=product.supplier_id,
        )
        db.session.add(duplicated)
        db.session.flush()

        for variant in product.variants:
            db.session.add(
                ProductVariant(
                    product_id=duplicated.id,
                    color_id=variant.color_id,
                    size_id=variant.size_id,
                    min_stock=variant.min_stock,
                )
            )

        for image in product.ordered_images:
            copied_filename = copiar_imagem_produto(image.filename)
            if copied_filename:
                db.session.add(
                    ProductImage(
                        product_id=duplicated.id,
                        filename=copied_filename,
                        position=image.position,
                        is_primary=image.is_primary,
                    )
                )

        db.session.commit()
        flash("Produto copiado. Revise nome, SKU, preco e ative no catalogo.")
        return redirect(url_for("edit_product", product_id=duplicated.id))

    @app.route("/produtos/<int:product_id>/excluir", methods=["POST"])
    @permission_required("produtos")
    def delete_product(product_id):
        product = db.get_or_404(Product, product_id)
        image_files = [image.filename for image in product.images]
        try:
            db.session.delete(product)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Nao foi possivel excluir: o produto possui movimentacoes ou vendas vinculadas.", "error")
            return redirect(url_for("products"))
        for filename in image_files:
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        flash("Produto excluido.")
        return redirect(url_for("products"))

    @app.route("/produtos/<int:product_id>/imagens", methods=["GET", "POST"])
    @permission_required("produtos")
    def product_images(product_id):
        product = db.get_or_404(Product, product_id)
        if request.method == "POST":
            saved_count = save_product_images(product, request.files.getlist("images"), request.form.get("primary_upload_index"))
            db.session.commit()
            flash(f"{saved_count} imagem(ns) adicionada(s).")
            return redirect(url_for("product_images", product_id=product.id))
        return render_template("product_images.html", product=product)

    @app.route("/produtos/imagens/<int:image_id>/principal", methods=["POST"])
    @permission_required("produtos")
    def set_primary_product_image(image_id):
        image = db.get_or_404(ProductImage, image_id)
        product = image.product
        for product_image in product.images:
            product_image.is_primary = product_image.id == image.id
        db.session.commit()
        flash("Imagem principal atualizada.")
        return redirect(request.referrer or url_for("product_images", product_id=product.id))

    @app.route("/produtos/imagens/<int:image_id>/excluir", methods=["POST"])
    @permission_required("produtos")
    def delete_product_image(image_id):
        image = db.get_or_404(ProductImage, image_id)
        filename = image.filename
        product_id = image.product_id
        was_primary = image.is_primary
        product = image.product
        db.session.delete(image)
        if was_primary:
            next_image = next((item for item in product.images if item.id != image.id), None)
            if next_image:
                next_image.is_primary = True
        db.session.commit()
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        flash("Imagem removida.")
        return redirect(url_for("product_images", product_id=product_id))

    @app.route("/produtos/<int:product_id>/variacao", methods=["POST"])
    @permission_required("produtos")
    def add_variant(product_id):
        db.session.add(
            ProductVariant(
                product_id=product_id,
                color_id=request.form.get("color_id") or None,
                size_id=request.form.get("size_id") or None,
                min_stock=int(request.form.get("min_stock") or 1),
            )
        )
        db.session.commit()
        flash("Variacao adicionada.")
        return redirect(url_for("edit_product", product_id=product_id))

    @app.route("/produtos/variacoes/<int:variant_id>/editar", methods=["POST"])
    @permission_required("produtos")
    def update_variant(variant_id):
        variant = db.get_or_404(ProductVariant, variant_id)
        variant.color_id = request.form.get("color_id") or None
        variant.size_id = request.form.get("size_id") or None
        variant.min_stock = int(request.form.get("min_stock") or 1)
        db.session.commit()
        flash("Variacao atualizada.")
        return redirect(url_for("edit_product", product_id=variant.product_id))

    @app.route("/produtos/variacoes/<int:variant_id>/excluir", methods=["POST"])
    @permission_required("produtos")
    def delete_variant(variant_id):
        variant = db.get_or_404(ProductVariant, variant_id)
        product_id = variant.product_id
        if variant.stock_movements or variant.sale_items:
            flash("Nao foi possivel excluir: a variacao possui estoque ou vendas vinculadas.", "error")
            return redirect(url_for("edit_product", product_id=product_id))
        db.session.delete(variant)
        db.session.commit()
        flash("Variacao excluida.")
        return redirect(url_for("edit_product", product_id=product_id))

    @app.route("/estoque", methods=["GET", "POST"])
    @permission_required("estoque")
    def stock():
        if request.method == "POST":
            quantity = int(request.form.get("quantity") or 0)
            if request.form["movement_type"] == "ajuste":
                variant = db.session.get(ProductVariant, int(request.form["variant_id"]))
                quantity = quantity - variant.stock
            preco_custo = (
                parse_decimal_br(request.form.get("preco_custo") or 0)
                if request.form["movement_type"] == "entrada"
                else None
            )
            db.session.add(
                StockMovement(
                    variant_id=int(request.form["variant_id"]),
                    movement_type=request.form["movement_type"],
                    quantity=quantity,
                    preco_custo=preco_custo,
                    note=request.form.get("note", "").strip(),
                )
            )
            db.session.commit()
            flash("Estoque atualizado.")
            return redirect(url_for("stock"))
        return render_template(
            "stock.html",
            variants=ProductVariant.query.join(Product).order_by(Product.name).all(),
        )

    @app.route("/estoque/movimentacoes")
    @permission_required("estoque")
    def stock_movements():
        page = request.args.get("page", 1, type=int)
        pagination = (
            StockMovement.query
            .join(ProductVariant)
            .join(Product)
            .order_by(StockMovement.created_at.desc())
            .paginate(page=page, per_page=20, error_out=False)
        )
        return render_template(
            "stock_movements.html",
            movements=pagination.items,
            pagination=pagination,
        )

    @app.route("/vendas", methods=["GET", "POST"])
    @permission_required("vendas")
    def sales():
        if request.method == "POST":
            variant_ids = request.form.getlist("variant_id")
            quantities = request.form.getlist("quantity")
            selected_items = []
            for variant_id, quantity in zip(variant_ids, quantities):
                try:
                    quantity_int = int(quantity or 0)
                except ValueError:
                    quantity_int = 0
                if not variant_id or quantity_int <= 0:
                    continue
                variant = db.session.get(ProductVariant, int(variant_id))
                if not variant:
                    continue
                if quantity_int > variant.stock:
                    flash(f"Estoque insuficiente para {variant.label}.", "error")
                    return redirect(url_for("sales"))
                selected_items.append((variant, quantity_int))
            if not selected_items:
                flash("Inclua pelo menos um item na venda.", "error")
                return redirect(url_for("sales"))
            sale = Sale(
                client_id=request.form.get("client_id") or None,
                discount=parse_decimal_br(request.form.get("discount") or 0),
                payment_method=request.form["payment_method"],
            )
            db.session.add(sale)
            for variant, quantity in selected_items:
                db.session.add(
                    SaleItem(
                        sale=sale,
                        variant=variant,
                        quantity=quantity,
                        preco_venda_unitario=variant.product.preco_venda,
                        preco_custo_unitario=custo_medio_variant(variant),
                    )
                )
            db.session.commit()
            flash("Venda registrada.")
            return redirect(url_for("receipt", sale_id=sale.id))
        return render_template(
            "sales.html",
            sales=Sale.query.order_by(Sale.created_at.desc()).limit(30).all(),
            clients=Client.query.order_by(Client.name).all(),
            variants=ProductVariant.query.join(Product).order_by(Product.name).all(),
        )

    @app.route("/vendas/<int:sale_id>/recibo")
    @permission_required("vendas")
    def receipt(sale_id):
        return render_template("receipt.html", sale=db.get_or_404(Sale, sale_id))

    @app.route("/catalogo")
    def catalog():
        settings = get_store_settings()
        whatsapp = settings.whatsapp_number or app.config["WHATSAPP_NUMBER"]
        search = request.args.get("q", "").strip()
        product_options = (
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.variants).selectinload(ProductVariant.color),
            selectinload(Product.variants).selectinload(ProductVariant.size),
            selectinload(Product.variants).selectinload(ProductVariant.stock_movements),
            selectinload(Product.variants).selectinload(ProductVariant.sale_items),
        )
        query = Product.query.filter_by(active=True).options(*product_options)
        featured_products = []
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
            products = query.order_by(Product.name).all()
        else:
            featured_products = query.filter_by(featured=True).order_by(Product.name).all()
            products = query.filter_by(featured=False).order_by(Product.name).all()
        return render_template("catalog.html", products=products, featured_products=featured_products, whatsapp=whatsapp, quote_plus=quote_plus, search=search, settings=settings)

    @app.route("/relatorios")
    @permission_required("relatorios")
    def reports():
        start = request.args.get("start")
        end = request.args.get("end")
        query = Sale.query
        if start:
            query = query.filter(func.date(Sale.created_at) >= datetime.strptime(start, "%Y-%m-%d").date())
        if end:
            query = query.filter(func.date(Sale.created_at) <= datetime.strptime(end, "%Y-%m-%d").date())
        sales_list = query.order_by(Sale.created_at.desc()).all()
        top_products = (
            db.session.query(Product.name, func.sum(SaleItem.quantity).label("qty"))
            .join(ProductVariant, SaleItem.variant_id == ProductVariant.id)
            .join(Product, ProductVariant.product_id == Product.id)
            .group_by(Product.name)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(10)
            .all()
        )
        low_stock = [v for v in ProductVariant.query.all() if v.stock <= v.min_stock]
        variants = ProductVariant.query.join(Product).order_by(Product.name).all()
        inventory_quantity = sum(max(variant.stock, 0) for variant in variants)
        inventory_cost_total = sum(custo_medio_variant(variant) * max(variant.stock, 0) for variant in variants)
        inventory_revenue_total = sum(variant.product.preco_venda * max(variant.stock, 0) for variant in variants)
        return render_template(
            "reports.html",
            sales=sales_list,
            total=sum(s.total for s in sales_list),
            custo_total=sum(sum(item.custo_total for item in sale.items) for sale in sales_list),
            lucro_total=sum(sum(item.lucro_total for item in sale.items) for sale in sales_list),
            inventory_quantity=inventory_quantity,
            inventory_cost_total=inventory_cost_total,
            inventory_revenue_total=inventory_revenue_total,
            inventory_potential_profit=inventory_revenue_total - inventory_cost_total,
            top_products=top_products,
            low_stock=low_stock,
            start=start,
            end=end,
        )

    @app.cli.command("seed")
    def seed_command():
        seed_data()
        print("Dados iniciais criados.")
