import os
from datetime import timedelta
from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.from_object("app.config.Config")
    app.config.setdefault("PERMANENT_SESSION_LIFETIME", timedelta(minutes=20))
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SECURE", False)  # Expect HTTPS in production
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("REMEMBER_COOKIE_HTTPONLY", True)

    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    from app import routes  # noqa: WPS433

    with app.app_context():
        db.create_all()

    app.register_blueprint(routes.bp)
    login_manager.login_view = "routes.login"

    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models import User  # noqa: WPS433

        return db.session.get(User, int(user_id))

    return app
