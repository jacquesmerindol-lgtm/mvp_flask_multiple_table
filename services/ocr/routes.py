# services/ocr/routes.py

from flask import Blueprint, render_template, request, redirect, url_for
from services.ocr.forms import ImageInitForm, SelectLivreForm
from services.ocr.pipeline.pipeline_ocr import run_pipeline_ocr
from services.ocr.pipeline.pipeline_structuration import run_pipeline_structuration
from services.ocr.pipeline.pipeline_save_db import run_pipeline_save_recettes
from services.schema import OCRResults, Recette
from services.service_instance import ocr_processor, structuration_processor
from services.ocr.utils import get_livres_choices
from app.redis_client import redis_client
import json

from services.ocr.redis_store import (
    load_ocr_from_redis,
    load_structuration_from_redis,
    save_structuration_to_redis,
    save_selected_livre_to_redis,
    load_selected_livre_from_redis,
)


bp = Blueprint("ocr", __name__, url_prefix="/ocr")


# @bp.route("/init", methods=["GET", "POST"])
# def init_ui():
#     form = ImageInitForm()

#     if form.validate_on_submit():
#         # Exécution du pipeline OCR
#         results = run_pipeline_ocr(
#             files=form.files.data,
#             use_llm=form.use_llm.data
#         )

#         # On stocke les résultats OCR dans la session pour le second service
#         session["ocr_results"] = results.model_dump()

#         return render_template("ocr/ocr_results.html", results=results)

#     return render_template("ocr/ocr_init.html", form=form)

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

# @bp.route("/structuration", methods=["POST"])
# def structuration_ui():
#     # Récupération des résultats OCR depuis la session
#     results_dict  = session.get("ocr_results")

#     if not results_dict :
#         return "Aucun résultat OCR disponible. Veuillez relancer l'analyse.", 400
    
#     ocr_results = OCRResults.model_validate(results_dict)

#     # Exécution du pipeline de structuration
#     structured = run_pipeline_structuration(ocr_results, schema_name="Recette")

#     # 🔥 AJOUT OBLIGATOIRE 
#     # session["structured_results"] = structured
#     session["structured_results"] = [item.model_dump() for item in structured]

    
#     # Affichage dans le template dédié
#     return render_template("ocr/structuration_results.html", results=structured)

from app.redis_client import redis_client


@bp.route("/structuration", methods=["POST"])
def structuration_ui():
    # 1) Récupération du résultat OCR depuis le processor
    # ocr_results = ocr_processor._output_model
    # 1) Charger OCR depuis Redis
    ocr_results = load_ocr_from_redis()
    if not ocr_results:
        return "Aucun résultat OCR disponible.", 400

    # if ocr_results is None:
    #     return "Aucun résultat OCR disponible. Veuillez relancer l'analyse.", 400

    # 2) Exécution du pipeline de structuration
    structured = run_pipeline_structuration(
        ocr_results,
        schema_name="Recette"
    )

    # 3) Sauvegarde Redis
    save_structuration_to_redis(structured)

    # 3) Affichage dans le template
    return render_template(
        "ocr/structuration_results.html",
        results=structured
    )


# @bp.route("/select_livre", methods=["GET", "POST"])
# def select_livre_ui():
#     structured = session.get("structured_results")
#     if not structured:
#         return "Aucune donnée structurée disponible.", 400

#     form = SelectLivreForm()
#     form.load_choices()  # 🔥 charge les choix lisibles

#     if form.validate_on_submit():
#         session["selected_livre"] = form.id_livre.data
#         return redirect(url_for("ocr.save_structured_ui"))

#     return render_template("ocr/select_livre.html", form=form)

@bp.route("/select_livre", methods=["GET", "POST"])
def select_livre_ui():
    # 1) Récupération des données structurées depuis le processor
    # structured = structuration_processor._output_model
    structured = load_structuration_from_redis()

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
        save_selected_livre_to_redis(int(selected_id))
        return redirect(url_for("ocr.save_structured_ui"))

    # 4) GET → afficher la page
    return render_template("ocr/select_livre.html", livres=livres)



# @bp.route("/save", methods=["GET", "POST"])
# def save_structured_ui():
#     structured = session.get("structured_results")
#     id_livre_reference = session.get("selected_livre")

#     if not structured or not id_livre_reference:
#         return "Données manquantes.", 400

#     saved = run_pipeline_save_recettes(structured, id_livre_reference)

#     return render_template("ocr/save_results.html", results=saved)

@bp.route("/save", methods=["GET", "POST"])
def save_structured_ui():
    # 1) Récupération des recettes structurées depuis le processor
    # structured = structuration_processor._output_model
     # 1) Charger OCR depuis Redis
    structured = load_structuration_from_redis()
    id_livre_reference = load_selected_livre_from_redis()

    # 2) Récupération de l’ID du livre depuis la session (léger → OK)
    # id_livre_reference = session.get("selected_livre")


    if not structured or not id_livre_reference:
        return "Données manquantes.", 400

    # 3) Exécution du pipeline de sauvegarde
    saved = run_pipeline_save_recettes(structured, id_livre_reference)

    # 4) Affichage du résultat
    return render_template("ocr/save_results.html", results=saved)

