# services/ocr/routes.py

from flask import Blueprint, render_template, request, session, redirect, url_for
from services.ocr.forms import ImageInitForm, SelectLivreForm
from services.ocr.pipeline.pipeline_ocr import run_pipeline_ocr
from services.ocr.pipeline.pipeline_structuration import run_pipeline_structuration
from services.ocr.pipeline.pipeline_save_db import run_pipeline_save_recettes

bp = Blueprint("ocr", __name__, url_prefix="/ocr")


@bp.route("/init", methods=["GET", "POST"])
def init_ui():
    form = ImageInitForm()

    if form.validate_on_submit():
        # Exécution du pipeline OCR
        results = run_pipeline_ocr(
            files=form.files.data,
            use_llm=form.use_llm.data
        )

        # On stocke les résultats OCR dans la session pour le second service
        session["ocr_results"] = results

        return render_template("ocr/ocr_results.html", results=results)

    return render_template("ocr/ocr_init.html", form=form)


@bp.route("/structuration", methods=["POST"])
def structuration_ui():
    # Récupération des résultats OCR depuis la session
    results = session.get("ocr_results")

    if not results:
        return "Aucun résultat OCR disponible. Veuillez relancer l'analyse.", 400

    # Exécution du pipeline de structuration
    structured = run_pipeline_structuration(results, schema_name="Recette")

    # 🔥 AJOUT OBLIGATOIRE 
    # session["structured_results"] = structured
    session["structured_results"] = [item.model_dump() for item in structured]

    
    # Affichage dans le template dédié
    return render_template("ocr/structuration_results.html", results=structured)


@bp.route("/select_livre", methods=["GET", "POST"])
def select_livre_ui():
    structured = session.get("structured_results")
    if not structured:
        return "Aucune donnée structurée disponible.", 400

    form = SelectLivreForm()
    form.load_choices()  # 🔥 charge les choix lisibles

    if form.validate_on_submit():
        session["selected_livre"] = form.id_livre.data
        return redirect(url_for("ocr.save_structured_ui"))

    return render_template("ocr/select_livre.html", form=form)

@bp.route("/save", methods=["GET", "POST"])
def save_structured_ui():
    structured = session.get("structured_results")
    id_livre_reference = session.get("selected_livre")

    if not structured or not id_livre_reference:
        return "Données manquantes.", 400

    saved = run_pipeline_save_recettes(structured, id_livre_reference)

    return render_template("ocr/save_results.html", results=saved)

