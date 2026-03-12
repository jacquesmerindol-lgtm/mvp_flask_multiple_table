from flask_wtf import FlaskForm
from wtforms import (
    StringField, HiddenField, SelectMultipleField,
    SelectField, IntegerField, SubmitField
)
from wtforms.validators import DataRequired, InputRequired, ValidationError
from database import get_db
from crud import livre_crud
from config import get_settings

settings = get_settings()

class LivreCreateForm(FlaskForm):
    nom_livre = StringField("Nom du livre", validators=[DataRequired()])
    numero_livre = StringField("Numéro (optionnel)")

    periode_recettes = SelectMultipleField(
        "Périodes",
        choices=[(m, m.capitalize()) for m in settings.PERIODES_LIST],
        coerce=str,
        validators=[InputRequired()]   # meilleur que DataRequired pour SelectMultipleField
    )

    nom_robot = SelectField(
        "Robot utilisé",
        choices=[(r, r) for r in settings.ROBOTS_LIST],
        coerce=str,
        validators=[InputRequired()]   # idem
    )

    submit = SubmitField("Créer")

    def validate_nom_livre(self, field):
        """Empêche la création d’un livre avec un nom déjà existant."""
        with get_db() as db:
            if livre_crud.exists(db, "nom_livre", field.data):
                raise ValidationError("Ce nom de livre existe déjà.")


class LivreUpdateForm(FlaskForm):
    id_livre = HiddenField()

    nom_livre = StringField("Nom du livre", validators=[DataRequired()])
    numero_livre = StringField("Numéro (optionnel)")

    periode_recettes = SelectMultipleField(
        "Périodes",
        choices=[(m, m.capitalize()) for m in settings.PERIODES_LIST],
        coerce=str,
        validators=[InputRequired()]
    )

    nom_robot = SelectField(
        "Robot utilisé",
        choices=[(r, r) for r in settings.ROBOTS_LIST],
        coerce=str,
        validators=[InputRequired()]
    )
    
    submit = SubmitField("Modifier")

    def validate_nom_livre(self, field):
        """Empêche de renommer un livre avec un nom déjà existant."""
        with get_db() as db:
            if livre_crud.exists(db, "nom_livre", field.data, exclude_id=self.id_livre.data):
                raise ValidationError("Ce nom de livre existe déjà.")


class LivreDeleteForm(FlaskForm):
    id_livre = HiddenField()


class LivreSearchForm(FlaskForm):
    id_livre = IntegerField("ID")
    nom_livre = StringField("Nom")
    numero_livre = StringField("Numéro")

    nom_robot = SelectField("Robot", choices=[], coerce=str)
    periode_recettes = SelectField("Période", choices=[], coerce=str)

    submit = SubmitField("Filtrer")
