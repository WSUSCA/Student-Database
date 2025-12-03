from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Optional

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db, login_manager
from app.forms import LoginForm, StudentForm
from app.models import AuditLog, Student, User

bp = Blueprint("routes", __name__)


def role_required(role: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            return func(*args, **kwargs)

        return wrapped

    return decorator


def log_action(user_id: int, action: str, student_id: Optional[int] = None) -> None:
    log_entry = AuditLog(user_id=user_id, action=action, student_id=student_id, timestamp=datetime.utcnow())
    db.session.add(log_entry)
    db.session.commit()


@bp.before_app_request
def enforce_session_timeout():
    session.permanent = True
    now = datetime.utcnow()
    last_seen = session.get("last_seen")
    if last_seen:
        elapsed = now - datetime.fromisoformat(last_seen)
        if elapsed > timedelta(minutes=30):
            logout_user()
            flash("Session timed out for security.", "warning")
            return redirect(url_for("routes.login"))
    session["last_seen"] = now.isoformat()


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            log_action(user.id, "LOGIN")
            return redirect(url_for("routes.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    log_action(current_user.id, "LOGOUT")
    logout_user()
    return redirect(url_for("routes.login"))


@bp.route("/")
@login_required
def dashboard():
    students = Student.query.all()
    return render_template("dashboard.html", students=students)


@bp.route("/students/<int:student_id>", methods=["GET", "POST"])
@login_required
def view_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    form = StudentForm(obj=student)

    if request.method == "GET":
        log_action(current_user.id, "VIEW_STUDENT", student_id=student.id)

    if form.validate_on_submit():
        if current_user.role not in {"admin", "staff"}:
            abort(403)
        student.name = form.name.data
        student.email = form.email.data
        student.status = form.status.data
        student.notes = form.notes.data
        student.goals = form.goals.data
        db.session.commit()
        log_action(current_user.id, "UPDATE_STUDENT", student_id=student.id)
        flash("Student updated", "success")
        return redirect(url_for("routes.view_student", student_id=student.id))

    return render_template("student_detail.html", student=student, form=form)


@bp.route("/admin/audit")
@login_required
@role_required("admin")
def view_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template("audit_logs.html", logs=logs)


@bp.route("/admin/create-user", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_user():
    form = LoginForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists", "warning")
        else:
            user = User(username=form.username.data, role="staff")
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            log_action(current_user.id, "CREATE_USER")
            flash("User created", "success")
            return redirect(url_for("routes.dashboard"))
    return render_template("create_user.html", form=form)


@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("Please log in to access this page", "warning")
    return redirect(url_for("routes.login"))
