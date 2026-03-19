from flask import Blueprint, render_template, request, redirect, url_for

from services.ocr.pipeline.pipeline_ocr import run_pipeline_ocr
from services.ocr.pipeline.pipeline_structuration import run_pipeline_structuration
from services.ocr.pipeline.pipeline_save_db import run_pipeline_save_recettes
from services.schema import OCRResults, Recette
from services.service_instance import ocr_processor, structuration_processor
from services.ocr.utils import get_livres_choices

from services.ocr.redis_store import (
    get_ocr_output,
    get_ocr_structuration_output,
    save_ocr_structuration_output,
    save_ocr_selected_livre,
    get_ocr_selected_livre,
)

bp = Blueprint("ocr", __name__, url_prefix="/ocr")


@bp.route("/init", methods=["GET", "POST"])
def init_ui():
    if request.method == "POST":
        # 1) Récupération des fichiers uploadés
        files = request.files.getlist("files")

        # 2) Récupération du booléen LLM
        use_llm = request.form.get("use_llm") == "on"

        # 3) Exécution du pipeline OCR
        results = run_pipeline_ocr(files=files, use_llm=use_llm)

        # 4) Affichage des résultats OCR
        return render_template("ocr/ocr_results.html", results=results)

    # GET → afficher le formulaire
    return render_template("ocr/ocr_init.html")


@bp.route("/structuration", methods=["POST"])
def structuration_ui():
    # 1) Récupération du résultat OCR depuis le processor
    # ocr_results = ocr_processor._output_model
    # 1) Charger OCR depuis Redis
    user_id = request.cookies.get("user_id")
    ocr_results = get_ocr_output(user_id)
    if not ocr_results:
        return "Aucun résultat OCR disponible.", 400

    # 2) Exécution du pipeline de structuration
    structured = run_pipeline_structuration(
        ocr_results,
        schema_name="Recette"
    )

    # 3) Sauvegarde Redis
    save_ocr_structuration_output(user_id, structured)

    # 4) Affichage dans le template
    return render_template(
        "ocr/structuration_results.html",
        results=structured
    )


@bp.route("/select_livre", methods=["GET", "POST"])
def select_livre_ui():
    # 1) Récupération des données structurées depuis Redis
    user_id = request.cookies.get("user_id")
    structured = get_ocr_structuration_output(user_id)

    if not structured:
        return "Aucune donnée structurée disponible.", 400

    # 2) Charger les choix de livres
    livres = get_livres_choices()

    if request.method == "POST":
        selected_id = request.form.get("id_livre")
        if not selected_id:
            return "Aucun livre sélectionné.", 400

        # 3) Stocker l’ID du livre choisi (session OK ici)
        # session["selected_livre"] = int(selected_id)
        user_id = request.cookies.get("user_id")
        save_ocr_selected_livre(user_id, int(selected_id))
        return redirect(url_for("ocr.save_structured_ui"))

    # 4) GET → afficher la page
    return render_template("ocr/select_livre.html", livres=livres)


@bp.route("/save", methods=["GET", "POST"])
def save_structured_ui():
    # 1) Récupération des recettes structurées depuis Redis
    user_id = request.cookies.get("user_id")
    structured = get_ocr_structuration_output(user_id)
    id_livre_reference = get_ocr_selected_livre(user_id)

    # 2) Récupération de l’ID du livre depuis la session (léger → OK)
    # id_livre_reference = session.get("selected_livre")

    if not structured or not id_livre_reference:
        return "Données manquantes.", 400

    # 3) Exécution du pipeline de sauvegarde
    saved = run_pipeline_save_recettes(structured, id_livre_reference)

    # 4) Affichage du résultat
    return render_template("ocr/save_results.html", results=saved)
