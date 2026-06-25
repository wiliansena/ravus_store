import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ravus_store"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "")
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@ravus.local")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "products")
    LOGO_UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "store")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
