"""Application entry point with secure defaults.

Usage:
    Local development (with test data):
        export FLASK_APP=run.py
        export FLASK_DEBUG=1
        export DATABASE_URL=sqlite:///student.db
        export SECRET_KEY="dev-secret-change"
        export ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
        flask run --host=0.0.0.0 --port=8000

    Production-like run (debug off, HTTPS-ready):
        export FLASK_APP=run.py
        export FLASK_DEBUG=0
        export SESSION_COOKIE_SECURE=1
        export SECRET_KEY="<strong-random>"
        export ENCRYPTION_KEY="<managed-32-byte-base64-key>"
        export DATABASE_URL="postgresql+psycopg2://user:password@host/dbname"
        flask run --host=0.0.0.0 --port=8000

Debug is disabled by default; environment variables must be provided for secrets.
"""

from app import create_app

app = create_app()


if __name__ == "__main__":
    app.run(debug=False)
