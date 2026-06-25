import os
import uuid

from flask import current_app
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename


THUMB_SIZE = (700, 875)


def extensao_permitida(filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return extension in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def product_thumb_filename(filename):
    stem = os.path.splitext(filename)[0]
    return f"{stem}.webp"


def gerar_thumbnail_produto(filename):
    source_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(source_path):
        return None

    os.makedirs(current_app.config["PRODUCT_THUMB_FOLDER"], exist_ok=True)
    thumb_filename = product_thumb_filename(filename)
    thumb_path = os.path.join(current_app.config["PRODUCT_THUMB_FOLDER"], thumb_filename)

    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        image.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
        image.save(thumb_path, "WEBP", quality=78, method=6)

    return thumb_filename


def salvar_upload_produto(arquivo):
    if not arquivo or not arquivo.filename:
        return None
    if not extensao_permitida(arquivo.filename):
        return None

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    original_name = secure_filename(arquivo.filename)
    extension = original_name.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    arquivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    gerar_thumbnail_produto(filename)
    return filename


def salvar_upload_logo(arquivo):
    if not arquivo or not arquivo.filename:
        return None
    if not extensao_permitida(arquivo.filename):
        return None

    os.makedirs(current_app.config["LOGO_UPLOAD_FOLDER"], exist_ok=True)
    original_name = secure_filename(arquivo.filename)
    extension = original_name.rsplit(".", 1)[-1].lower()
    filename = f"logo-{uuid.uuid4().hex}.{extension}"
    arquivo.save(os.path.join(current_app.config["LOGO_UPLOAD_FOLDER"], filename))
    return filename
