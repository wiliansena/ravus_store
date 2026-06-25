import argparse
import os

from flask import Flask

from config import Config
from extensions import db, login_manager, migrate
from routes import register_routes
from services import get_store_settings, money, seed_data
from datetime_utils import format_datetime_brazil


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["LOGO_UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Entre para acessar o sistema."

    app.jinja_env.filters["money"] = money
    app.jinja_env.filters["datetime_br"] = format_datetime_brazil

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_store_settings():
        try:
            return {"store_settings": get_store_settings()}
        except Exception:
            return {"store_settings": None}

    register_routes(app)
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-db", action="store_true")
    args = parser.parse_args()
    app = create_app()
    if args.init_db:
        with app.app_context():
            db.create_all()
            seed_data()
        print("Banco inicializado.")
    else:
        app.run(debug=True)
