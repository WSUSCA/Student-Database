from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])


class StudentForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    status = SelectField(
        "Status",
        choices=[("active", "Active"), ("inactive", "Inactive"), ("alumni", "Alumni")],
    )
    notes = TextAreaField("Notes", validators=[Length(max=2000)])
    goals = TextAreaField("Goals", validators=[Length(max=2000)])
