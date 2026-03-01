from wtforms import MultipleFileField
from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired

from services.ocr.utils import get_livres_choices


class ImageInitForm(FlaskForm):
    files = MultipleFileField("Images", validators=[DataRequired()])
    use_llm = BooleanField("Activer LLM ?", default=False)
    submit = SubmitField("Valider")


class SelectLivreForm(FlaskForm):
    id_livre = SelectField("Choisir un livre", coerce=int)
    submit = SubmitField("Enregistrer les recettes")

    def load_choices(self):
        self.id_livre.choices = get_livres_choices()
