from datetime import datetime, timedelta
from functools import wraps
from typing import Callable

import bcrypt
from flask import abort, current_app, flash, redirect, request, session, url_for
from flask_login import LoginManager, current_user, login_user, logout_user

from models import User, db

login_manager = LoginManager()
login_manager.login_view = "login"

SESSION_TIMEOUT_MINUTES = 30


def init_auth(app):
    login_manager.init_app(app)

    @app.before_request
    def enforce_session_timeout():
        if not current_user.is_authenticated:
            return
        now = datetime.utcnow()
        last = session.get("last_active")
        if last:
            last_dt = datetime.fromisoformat(last)
            if now - last_dt > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                logout_user()
                flash("Session timed out for security. Please log in again.", "warning")
                return redirect(url_for("login"))
        session["last_active"] = now.isoformat()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def role_required(role: str) -> Callable:
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("login"))
            if current_user.role != role:
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator
