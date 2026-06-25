import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename


def extensao_permitida(filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return extension in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


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
