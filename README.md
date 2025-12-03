# Student Database (Secure Pilot)

This Flask application demonstrates a student records portal built with privacy-first, FERPA/HIPAA-inspired safeguards.

## Security and compliance highlights
- Staff-only authentication using hashed passwords (bcrypt) and session cookies.
- Role-based access control: admins manage staff accounts and audit logs; staff edit student records.
- CSRF protection on all forms via Flask-WTF.
- Field-level encryption for sensitive text (notes/goals) using Fernet keys loaded from `ENCRYPTION_KEY` environment variable.
- Audit logging for key actions (login, viewing student details, updating students, creating users).
- Session timeout enforced after 30 minutes of inactivity.
- Database and secrets configured through environment variables; debug off by default.

## Running locally with test data
1. Create a virtual environment and install dependencies: `pip install -r requirements.txt`.
2. Export environment variables:
   - `FLASK_APP=run.py`
   - `FLASK_DEBUG=1` (optional for dev)
   - `SECRET_KEY` (random string for sessions)
   - `ENCRYPTION_KEY` (use `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
   - `DATABASE_URL=sqlite:///student.db` (or another SQLAlchemy URL)
3. Initialize the database by launching the app once or running `python -c "from run import app; app.app_context().push(); from app import db; db.create_all()"`.
4. Add an initial admin user in a Python shell:
   ```python
   from run import app
   from app import db
   from app.models import User
   with app.app_context():
       admin = User(username="admin", role="admin")
       admin.set_password("ChangeMe123!")
       db.session.add(admin)
       db.session.commit()
   ```
5. Start the server: `flask run --host=0.0.0.0 --port=8000`. Access via `http://localhost:8000/login`.

## Production-style guidance
- Keep `FLASK_DEBUG=0` (default) and set `SESSION_COOKIE_SECURE=1` behind HTTPS.
- Provide strong values for `SECRET_KEY` and `ENCRYPTION_KEY` via a secret manager or environment configuration.
- Point `DATABASE_URL` to your managed database; SQLAlchemy uses parameterized queries by default.
- Do not log sensitive student content; audit logs record actions only.
- Run behind an HTTPS termination point; avoid mixed-content URLs so the site remains protocol-agnostic.

## Notes
- Sensitive fields are encrypted at rest. Changing the `ENCRYPTION_KEY` will prevent decrypting existing records.
- The code avoids hard-coded credentials; ensure environment variables are provided before running.
