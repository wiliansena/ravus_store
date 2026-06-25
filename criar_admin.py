from app import create_app
from config import Config
from extensions import db
from models import Role, User
from werkzeug.security import generate_password_hash


def criar_admin():
    app = create_app()
    with app.app_context():
        role = Role.query.filter_by(name="Administrador").first()
        if not role:
            role = Role(name="Administrador")
            db.session.add(role)
            db.session.flush()

        email = Config.ADMIN_EMAIL.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            user.name = Config.ADMIN_NAME
            user.password_hash = generate_password_hash(Config.ADMIN_PASSWORD)
            user.active = True
            user.role = role
            message = f"Admin atualizado: {email}"
        else:
            db.session.add(
                User(
                    name=Config.ADMIN_NAME,
                    email=email,
                    password_hash=generate_password_hash(Config.ADMIN_PASSWORD),
                    active=True,
                    role=role,
                )
            )
            message = f"Admin criado: {email}"

        db.session.commit()
        print(message)


if __name__ == "__main__":
    criar_admin()
