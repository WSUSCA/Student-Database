import os
from datetime import datetime
from io import BytesIO

import pandas as pd
from dotenv import load_dotenv
from flask import (Flask, flash, redirect, render_template, request, send_file,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import CSRFProtect
from werkzeug.utils import secure_filename

from auth import hash_password, init_auth, role_required, verify_password
from forms import (
    GoalForm,
    ImportForm,
    LoginForm,
    NoteForm,
    PhaseUpdateForm,
    StudentForm,
    VisitForm,
)
from models import AuditLog, Goal, JourneyHistory, Note, Student, User, Visit, db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///career_companion.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB limit for uploads
app.config["REMEMBER_COOKIE_DURATION"] = 1800

csrf = CSRFProtect(app)
db.init_app(app)
init_auth(app)


@app.cli.command("init-db")
def init_db_command():
    """Initialize the database tables."""
    with app.app_context():
        db.create_all()
        print("Database initialized.")


@app.cli.command("create-admin")
def create_admin():
    """Create a default admin user for development."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "changeme")
    with app.app_context():
        if db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none():
            print("Admin already exists")
            return
        user = User(username=username, password_hash=hash_password(password), role="admin")
        db.session.add(user)
        db.session.commit()
        print(f"Admin user '{username}' created with provided password.")


def log_action(user_id, student_id, action, details=None):
    entry = AuditLog(user_id=user_id, student_id=student_id, action=action, details=details)
    db.session.add(entry)
    db.session.commit()


def str_to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


@app.route("/")
@login_required
def dashboard():
    phase_counts = dict(db.session.query(Student.current_phase, db.func.count(Student.id)).group_by(Student.current_phase).all())
    college_counts = dict(db.session.query(Student.college, db.func.count(Student.id)).group_by(Student.college).all())

    # Matrix of college x phase counts
    matrix = {}
    colleges = sorted({c for c in college_counts.keys() if c})
    phases = ["Need to Know", "Experience", "Act"]
    for college in colleges:
        matrix[college] = {}
        for phase in phases:
            count = (
                db.session.query(db.func.count(Student.id))
                .filter(Student.college == college, Student.current_phase == phase)
                .scalar()
            )
            matrix[college][phase] = count

    # Filters
    phase_filter = request.args.get("phase")
    college_filter = request.args.get("college")
    major_filter = request.args.get("major")
    alumni_filter = request.args.get("alumni")

    students_query = Student.query
    if phase_filter:
        students_query = students_query.filter(Student.current_phase == phase_filter)
    if college_filter:
        students_query = students_query.filter(Student.college == college_filter)
    if major_filter:
        students_query = students_query.filter(Student.major.ilike(f"%{major_filter}%"))
    if alumni_filter == "true":
        students_query = students_query.filter(Student.is_alumni.is_(True))
    elif alumni_filter == "false":
        students_query = students_query.filter(Student.is_alumni.is_(False))

    students = students_query.limit(50).all()

    return render_template(
        "dashboard.html",
        phase_counts=phase_counts,
        college_counts=college_counts,
        matrix=matrix,
        phases=phases,
        students=students,
        filters={
            "phase": phase_filter,
            "college": college_filter,
            "major": major_filter,
            "alumni": alumni_filter,
        },
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(username=form.username.data)).scalar_one_or_none()
        if user and verify_password(form.password.data, user.password_hash):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out securely.", "info")
    return redirect(url_for("login"))


@app.route("/students")
@login_required
def students():
    query = Student.query
    search = request.args.get("q")
    phase = request.args.get("phase")
    college = request.args.get("college")
    alumni = request.args.get("alumni")

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.first_name.ilike(like),
                Student.last_name.ilike(like),
                Student.email.ilike(like),
                Student.wsu_id.ilike(like),
            )
        )
    if phase:
        query = query.filter(Student.current_phase == phase)
    if college:
        query = query.filter(Student.college == college)
    if alumni == "true":
        query = query.filter(Student.is_alumni.is_(True))
    elif alumni == "false":
        query = query.filter(Student.is_alumni.is_(False))

    students = query.order_by(Student.last_name).limit(200).all()
    return render_template("students.html", students=students)


@app.route("/students/<int:student_id>", methods=["GET", "POST"])
@login_required
def student_detail(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        flash("Student not found", "warning")
        return redirect(url_for("students"))

    student_form = StudentForm(obj=student)
    phase_form = PhaseUpdateForm(current_phase=student.current_phase)
    goal_form = GoalForm()
    note_form = NoteForm()
    visit_form = VisitForm()

    if "save_student" in request.form and student_form.validate_on_submit():
        student_form.populate_obj(student)
        student.updated_at = datetime.utcnow()
        db.session.commit()
        log_action(current_user.id, student.id, "UPDATE_STUDENT", "Updated profile details")
        flash("Student updated", "success")
        return redirect(url_for("student_detail", student_id=student.id))

    if "update_phase" in request.form and phase_form.validate_on_submit():
        previous_phase = student.current_phase
        student.current_phase = phase_form.current_phase.data
        student.phase_date = datetime.utcnow()
        history = JourneyHistory(
            student_id=student.id,
            phase=student.current_phase,
            source="Manual",
            date_recorded=datetime.utcnow(),
            notes=f"Phase changed from {previous_phase} to {student.current_phase}",
        )
        db.session.add(history)
        db.session.commit()
        log_action(current_user.id, student.id, "UPDATE_PHASE", history.notes)
        flash("Phase updated", "success")
        return redirect(url_for("student_detail", student_id=student.id))

    if "add_goal" in request.form and goal_form.validate_on_submit():
        goal = Goal(
            student_id=student.id,
            goal_type=goal_form.goal_type.data,
            description=goal_form.description.data,
            target_date=goal_form.target_date.data,
            status=goal_form.status.data,
        )
        db.session.add(goal)
        db.session.commit()
        log_action(current_user.id, student.id, "ADD_GOAL", f"Goal: {goal.goal_type}")
        flash("Goal added", "success")
        return redirect(url_for("student_detail", student_id=student.id))

    if "add_note" in request.form and note_form.validate_on_submit():
        note = Note(
            student_id=student.id,
            author=note_form.author.data,
            note_type=note_form.note_type.data,
            content="",
        )
        note.set_content(note_form.content.data)
        db.session.add(note)
        db.session.commit()
        log_action(current_user.id, student.id, "ADD_NOTE", f"Note type: {note.note_type}")
        flash("Note added securely", "success")
        return redirect(url_for("student_detail", student_id=student.id))

    if "add_visit" in request.form and visit_form.validate_on_submit():
        visit = Visit(
            student_id=student.id,
            date=visit_form.date.data,
            visit_type=visit_form.visit_type.data,
            topic=visit_form.topic.data,
            staff=visit_form.staff.data,
            follow_up_needed=visit_form.follow_up_needed.data,
            follow_up_due=visit_form.follow_up_due.data,
        )
        db.session.add(visit)
        db.session.commit()
        log_action(current_user.id, student.id, "ADD_VISIT", f"Visit type: {visit.visit_type}")
        flash("Visit logged", "success")
        return redirect(url_for("student_detail", student_id=student.id))

    if request.method == "GET":
        log_action(current_user.id, student.id, "VIEW_STUDENT", "Viewed student profile")

    return render_template(
        "student_detail.html",
        student=student,
        student_form=student_form,
        phase_form=phase_form,
        goal_form=goal_form,
        note_form=note_form,
        visit_form=visit_form,
    )


@app.route("/import", methods=["GET", "POST"])
@login_required
@role_required("admin")
def import_students():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        if not filename:
            flash("Invalid file", "danger")
            return redirect(url_for("import_students"))
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        if filename.lower().endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)

        for _, row in df.iterrows():
            wsu_id = str(row.get("wsu_id")).strip()
            if not wsu_id or wsu_id.lower() == "nan":
                continue
            student = db.session.execute(db.select(Student).filter_by(wsu_id=wsu_id)).scalar_one_or_none()
            if not student:
                student = Student(wsu_id=wsu_id)
                db.session.add(student)

            student.first_name = row.get("first_name", "")
            student.last_name = row.get("last_name", "")
            student.email = row.get("email", "")
            student.major = row.get("major", "")
            student.college = row.get("college", "")
            student.class_standing = row.get("class_standing", "")
            student.first_gen = str_to_bool(row.get("first_gen", False))
            student.current_phase = row.get("current_phase", student.current_phase)
            student.is_alumni = str_to_bool(row.get("is_alumni", False))
            student.graduation_term = row.get("graduation_term", "")
            student.phase_date = datetime.utcnow()

            phase_value = row.get("current_phase")
            if phase_value:
                history = JourneyHistory(
                    student=student,
                    phase=phase_value,
                    source="ShockerCentral" if "shocker" in filename.lower() else "Manual",
                    date_recorded=datetime.utcnow(),
                    notes="Imported phase",
                )
                db.session.add(history)

        db.session.commit()
        flash("Import completed", "success")
        return redirect(url_for("dashboard"))

    return render_template("import.html", form=form)


@app.route("/export")
@login_required
@role_required("admin")
def export_students():
    phase = request.args.get("phase")
    college = request.args.get("college")
    alumni = request.args.get("alumni")

    query = Student.query
    if phase:
        query = query.filter(Student.current_phase == phase)
    if college:
        query = query.filter(Student.college == college)
    if alumni == "true":
        query = query.filter(Student.is_alumni.is_(True))
    elif alumni == "false":
        query = query.filter(Student.is_alumni.is_(False))

    students = query.all()
    data = [
        {
            "wsu_id": s.wsu_id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "email": s.email,
            "major": s.major,
            "college": s.college,
            "class_standing": s.class_standing,
            "first_gen": s.first_gen,
            "current_phase": s.current_phase,
            "is_alumni": s.is_alumni,
            "graduation_term": s.graduation_term,
        }
        for s in students
    ]
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return send_file(output, as_attachment=True, download_name=f"career_companion_export_{timestamp}.csv", mimetype="text/csv")


@app.route("/audit")
@login_required
@role_required("admin")
def audit_logs():
    user_filter = request.args.get("user")
    action_filter = request.args.get("action")
    start = request.args.get("start")
    end = request.args.get("end")

    query = AuditLog.query.order_by(AuditLog.timestamp.desc())
    if user_filter:
        query = query.join(User).filter(User.username == user_filter)
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if start:
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(start))
    if end:
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(end))

    logs = query.limit(200).all()
    users = db.session.query(User.username).all()
    return render_template("audit_logs.html", logs=logs, users=[u[0] for u in users])


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


@app.template_filter("phase_badge")
def phase_badge(phase):
    mapping = {
        "Need to Know": "badge bg-dark text-white",
        "Experience": "badge phase-experience",
        "Act": "badge phase-act",
    }
    return mapping.get(phase, "badge bg-secondary")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
