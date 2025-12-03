import os
from datetime import datetime
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates

# SQLAlchemy instance for use across the app
# Initialized in app.py

db = SQLAlchemy()


def _get_fernet() -> Fernet:
    """Return a Fernet instance using the encryption key from the environment.

    The environment variable `NOTE_ENCRYPTION_KEY` must contain a base64-encoded
    32-byte key. For development, generate one with `python -c "from
    cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
    and place it in a .env file.
    """

    key = os.getenv("NOTE_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("NOTE_ENCRYPTION_KEY not set. Configure encryption key in .env")
    return Fernet(key)


def encrypt_text(plain_text: str) -> str:
    if plain_text is None:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt_text(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    fernet = _get_fernet()
    try:
        return fernet.decrypt(cipher_text.encode()).decode()
    except (InvalidToken, ValueError):
        return "[Decryption error]"


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wsu_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    major = db.Column(db.String(120))
    college = db.Column(db.String(120))
    class_standing = db.Column(db.String(50))
    first_gen = db.Column(db.Boolean, default=False)
    current_phase = db.Column(db.String(50), default="Need to Know")
    phase_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_alumni = db.Column(db.Boolean, default=False)
    graduation_term = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    journey_history = db.relationship("JourneyHistory", backref="student", cascade="all, delete-orphan")
    goals = db.relationship("Goal", backref="student", cascade="all, delete-orphan")
    notes = db.relationship("Note", backref="student", cascade="all, delete-orphan")
    visits = db.relationship("Visit", backref="student", cascade="all, delete-orphan")
    audit_logs = db.relationship("AuditLog", backref="student")

    def __repr__(self):
        return f"<Student {self.wsu_id} {self.first_name} {self.last_name}>"

    @validates("email")
    def validate_email(self, key, address):
        if address and "@" not in address:
            raise ValueError("Invalid email address")
        return address


class JourneyHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    phase = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(50), default="Manual")
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    goal_type = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    target_date = db.Column(db.Date)
    status = db.Column(db.String(50), default="Not Started")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    note_type = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_content(self, plain_text: str):
        self.content = encrypt_text(plain_text)

    def get_content(self) -> str:
        return decrypt_text(self.content)


class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    visit_type = db.Column(db.String(120), nullable=False)
    topic = db.Column(db.String(200))
    staff = db.Column(db.String(120))
    follow_up_needed = db.Column(db.Boolean, default=False)
    follow_up_due = db.Column(db.Date)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="staff")

    audit_logs = db.relationship("AuditLog", backref="user")

    # Flask-Login integration
    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"))
    action = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)


# Placeholder stubs for future Shocker Central integration

def import_from_shocker_central_csv(file_path: str):
    """Placeholder for reading Shocker Central CSV exports.

    Implement CSV parsing and mapping to Student fields here. This stub is
    intentionally non-functional for security and development purposes.
    """
    raise NotImplementedError("Shocker Central CSV import not yet implemented")


def export_for_shocker_central() -> str:
    """Placeholder for exporting data in Shocker Central-compatible CSV.

    Should return a path to the generated CSV file once implemented.
    """
    raise NotImplementedError("Shocker Central export not yet implemented")


def push_update_to_shocker_central(student_id: int):
    """Placeholder for pushing updates to Shocker Central via API.

    An authenticated API call would go here once campus IT finalizes specs.
    """
    raise NotImplementedError("Shocker Central API integration not yet implemented")
