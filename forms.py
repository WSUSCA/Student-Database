from datetime import date
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DateTimeField, FileField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional

PHASE_CHOICES = [
    ("Need to Know", "Need to Know"),
    ("Experience", "Experience"),
    ("Act", "Act"),
]

STATUS_CHOICES = [
    ("Not Started", "Not Started"),
    ("In Progress", "In Progress"),
    ("Completed", "Completed"),
]


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


class StudentForm(FlaskForm):
    wsu_id = StringField("WSU ID", validators=[DataRequired()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[Email(), DataRequired()])
    major = StringField("Major")
    college = StringField("College")
    class_standing = StringField("Class Standing")
    first_gen = BooleanField("First Gen")
    current_phase = SelectField("Current Phase", choices=PHASE_CHOICES)
    is_alumni = BooleanField("Alumni")
    graduation_term = StringField("Graduation Term")
    submit = SubmitField("Save")


class PhaseUpdateForm(FlaskForm):
    current_phase = SelectField("Current Phase", choices=PHASE_CHOICES, validators=[DataRequired()])
    submit = SubmitField("Update Phase")


class GoalForm(FlaskForm):
    goal_type = StringField("Goal Type", validators=[DataRequired()])
    description = TextAreaField("Description")
    target_date = DateField("Target Date", validators=[Optional()])
    status = SelectField("Status", choices=STATUS_CHOICES)
    submit = SubmitField("Save Goal")


class NoteForm(FlaskForm):
    author = StringField("Author", validators=[DataRequired()])
    note_type = StringField("Note Type", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    submit = SubmitField("Add Note")


class VisitForm(FlaskForm):
    date = DateField("Date", default=date.today, validators=[DataRequired()])
    visit_type = StringField("Visit Type", validators=[DataRequired()])
    topic = StringField("Topic")
    staff = StringField("Staff")
    follow_up_needed = BooleanField("Follow-up Needed")
    follow_up_due = DateField("Follow-up Due", validators=[Optional()])
    submit = SubmitField("Log Visit")


class ImportForm(FlaskForm):
    file = FileField("Upload CSV/XLSX", validators=[DataRequired()])
    submit = SubmitField("Import")
