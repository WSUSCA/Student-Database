import os
from pathlib import Path


class Config:
    """Flask configuration focused on secure defaults.

    Notes for deployment:
    - Ensure the database URL is provided via the DATABASE_URL environment variable.
    - Set FLASK_DEBUG to "0" (default) for production-like environments.
    - Provide a strong, base64-encoded 32-byte Fernet key via ENCRYPTION_KEY.
    - Configure a secure secret key using the SECRET_KEY environment variable.
    """

    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{Path('student.db').absolute()}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    REMEMBER_COOKIE_DURATION = 1200  # 20 minutes
