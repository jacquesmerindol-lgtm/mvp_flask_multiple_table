# forms/courses.py
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired

class GenerateCourseForm(FlaskForm):
    recettes_json = TextAreaField("Recettes (JSON)", validators=[DataRequired()])
    submit = SubmitField("Générer la liste de courses")
