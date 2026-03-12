from flask_wtf import FlaskForm
from wtforms import (
    StringField, HiddenField, SelectField,
    TextAreaField, IntegerField, SubmitField
)
from wtforms.validators import DataRequired,ValidationError, Optional

from config import get_settings
from database import get_db
from models import Livre
from crud import recette_crud

settings = get_settings()


def get_livres_choices():
    """
    Renvoie une liste de tuples :
    [(id_livre, "numéro — nom"), ...]
    Les livres sont triés par numéro puis par nom.
    """
    with get_db() as db:
        livres = db.query(Livre).order_by(Livre.numero_livre, Livre.nom_livre).all()
        return [
            (l.id_livre, f"{l.numero_livre or 'N/A'} — {l.nom_livre}")
            for l in livres
        ]


class RecetteCreateForm(FlaskForm):
    nom_recette = StringField("Nom", validators=[DataRequired()])

    type_recette = SelectField(
        "Type",
        choices=[(t, t) for t in settings.RECETTE_TYPES],
        coerce=str,
        validators=[DataRequired()]
    )

    nombre_personnes = IntegerField("Personnes", validators=[DataRequired()])

    duree_preparation = StringField("Préparation (min)", validators=[DataRequired()])
    duree_cuisson = StringField("Cuisson (min)")
    duree_repos = StringField("Repos (min)")

    liste_ingredients = TextAreaField(
        "Ingrédients (JSON)",
        render_kw={"rows": 5},
        description='Format: [{"quantite": "200g", "unite": "g", "ingredient": "poulet"}]'
    )

    instructions = TextAreaField("Instructions", render_kw={"rows": 4})
    astuce = TextAreaField("Astuce", render_kw={"rows": 2})

    id_livre_reference = SelectField(
        "Livre référent",
        choices=[],          # rempli dynamiquement
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Créer")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_livre_reference.choices = get_livres_choices()

    def validate_nom_recette(self, field):
        """Empêche la création d’une recette avec un nom déjà existant."""
        with get_db() as db:
            if recette_crud.exists(db, "nom_recette", field.data):
                raise ValidationError("Ce nom de recette existe déjà.")


class RecetteUpdateForm(FlaskForm):
    id_recette = HiddenField()

    nom_recette = StringField("Nom", validators=[DataRequired()])

    type_recette = SelectField(
        "Type",
        choices=[(t, t) for t in settings.RECETTE_TYPES],
        coerce=str,
        validators=[DataRequired()]
    )

    nombre_personnes = IntegerField("Personnes", validators=[DataRequired()])

    duree_preparation = StringField("Préparation (min)", validators=[DataRequired()])
    duree_cuisson = StringField("Cuisson (min)")
    duree_repos = StringField("Repos (min)")

    liste_ingredients = TextAreaField(
        "Ingrédients (JSON)", render_kw={"rows": 5},
        description='Format: [{"quantite": "200g", "unite": "g", "ingredient": "poulet"}]'
    )

    instructions = TextAreaField("Instructions",render_kw={"rows": 4})   # ← hauteur du textarea
    astuce = TextAreaField("Astuce", render_kw={"rows": 2})

    id_livre_reference = SelectField(
        "Livre référent",
        choices=[],          # rempli dynamiquement
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Modifier")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_livre_reference.choices = get_livres_choices()

    def validate_nom_livre(self, field):
        """Empêche de renommer une recette avec un nom déjà existant."""
        with get_db() as db:
            if recette_crud.exists(db, "nom_recette", field.data, exclude_id=self.id_livre.data):
                raise ValidationError("Ce nom de livre existe déjà.")


class RecetteDeleteForm(FlaskForm):
    id_recette = HiddenField()


# class RecetteSearchForm(FlaskForm):
#     id_recette = IntegerField("ID")

class RecetteSearchForm(FlaskForm):
    id_recette = IntegerField("ID")
    nom_recette = StringField("Nom")
    type_recette = SelectField("Type", choices=[], coerce=str)
    nombre_personnes = IntegerField("Personnes")
    id_livre_reference = SelectField("Livre", coerce=int)
    submit = SubmitField("Filtrer")

