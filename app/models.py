from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from sqlalchemy.orm import validates

from app import bcrypt, db
from app.encryption import decrypt_text, encrypt_text, EncryptionError


class User(db.Model, UserMixin):  # type: ignore[misc]
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")

    def set_password(self, password: str) -> None:
        self.hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.hashed_password, password)


class Student(db.Model):  # type: ignore[misc]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="active")
    notes_encrypted = db.Column(db.Text, nullable=True)
    goals_encrypted = db.Column(db.Text, nullable=True)

    @property
    def notes(self) -> Optional[str]:
        return decrypt_text(self.notes_encrypted)

    @notes.setter
    def notes(self, value: Optional[str]) -> None:
        self.notes_encrypted = encrypt_text(value)

    @property
    def goals(self) -> Optional[str]:
        return decrypt_text(self.goals_encrypted)

    @goals.setter
    def goals(self, value: Optional[str]) -> None:
        self.goals_encrypted = encrypt_text(value)


class AuditLog(db.Model):  # type: ignore[misc]
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", lazy="joined")
    student = db.relationship("Student", lazy="joined")


@validates("role")
def validate_role(_key, value):
    if value not in {"admin", "staff"}:
        raise ValueError("Invalid role")
    return value
