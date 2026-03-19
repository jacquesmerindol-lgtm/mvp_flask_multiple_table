from flask_wtf import FlaskForm
from wtforms import (HiddenField, IntegerField, 
                     SubmitField, DateField, TextAreaField
                    )
from wtforms.validators import DataRequired
from app.database import get_db
from app.crud import course_crud
from app.config import get_settings

settings = get_settings()

class CourseBaseForm(FlaskForm):
    date_liste_course = DateField(
        "Date de la liste de course",
        format="%Y-%m-%d",
        validators=[DataRequired()]
    )

    # JSON stocké en base → textarea pour éditer proprement
    liste_recette = TextAreaField(
        "Liste de recettes (JSON)",
        render_kw={"rows": 5},
        validators=[DataRequired()]
    )

    liste_course = TextAreaField(
        "Liste de course (texte)",
        render_kw={"rows": 5},
        validators=[DataRequired()]
    )

    submit = SubmitField()

class CourseCreateForm(CourseBaseForm):
    submit = SubmitField("Créer")

class CourseUpdateForm(CourseBaseForm):
    id_course = HiddenField()

    submit = SubmitField("Modifier")

class CourseDeleteForm(FlaskForm):
    id_course = HiddenField()

class CourseSearchForm(FlaskForm):
    id_course = IntegerField("ID")
    date_liste_course = DateField("Date", format="%Y-%m-%d")

    submit = SubmitField("Filtrer")

    
     