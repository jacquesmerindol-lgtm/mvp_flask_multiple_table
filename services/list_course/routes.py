from flask import Blueprint, render_template, request, session, redirect, url_for, flash

import json

from services.list_course.forms import GenerateCourseForm
from models import Course
from services.list_course.schema import RecetteSelection
from database import get_db
from services.list_course.pipeline import pipeline
from crud import course_crud   
from sqlalchemy.exc import IntegrityError
from services.list_ingredients.logic import build_selection_pydantic

list_course_bp = Blueprint("list_courses", __name__, url_prefix="/list_courses")

# @courses_bp.route("/generate", methods=["GET", "POST"])
# def generate():
#     form = GenerateCourseForm()

#     if form.validate_on_submit():
#         try:
#             # 1. Charger le JSON
#             raw = form.recettes_json.data
#             data = json.loads(raw)

#             # 2. Construire les objets RecetteSelection
#             recettes = [RecetteSelection(**item) for item in data]

#             # 3. Appeler ton pipeline
#             result = pipeline(recettes)

#             # 4. Enregistrer dans ta table SQLAlchemy
#             with get_db() as db:
#                 new_course = Course(
#                     date_liste_course=result.date_liste_course,
#                     liste_recette=result.liste_recette,   # dict/list → JSON
#                     liste_course=result.liste_course      # string
#                 )
#                 db.add(new_course)
#                 db.commit()
#                 id_course = new_course.id_course

#             flash("Liste de course générée et enregistrée.", "success")
#             return redirect(url_for("courses.detail", id_course=id_course))

#         except Exception as e:
#             flash(f"Erreur : {e}", "danger")

#     return render_template("courses/generate.html", form=form)

@list_course_bp.route("/generate", methods=["GET", "POST"])
def generate():
    # 1. Récupération des recettes depuis la sessio
    session_data_out = session.get("liste_courses", {})
    print(session_data_out)
    print(type(session_data_out))

    # ----------------------------------------------------------------------
    # POST : ajout de recettes à la sélection (avec addition des quantités)
    # ----------------------------------------------------------------------
    if request.method == "POST":
        # 1. Récupération des recettes depuis la session
        session_data_in = session.get("liste_recettes")
        pydantic_data_in = build_selection_pydantic(session_data_in)
        print(session_data_in)
        print(type(session_data_in))
        print(pydantic_data_in)
        print(type(pydantic_data_in))
        if not session_data_in:
            flash("Aucune liste disponible. Veuillez sélectionner des recettes.", "warning")
            return redirect(url_for("recettes.index"))
        try:
            # 3. Appel du pipeline
            results = pipeline(pydantic_data_in)
            session["liste_courses"] = results.model_dump()
            # 4. Enregistrement via ton CRUD (pas de Course() manuel)
            with get_db() as db:
                course_crud.create(db, results.model_dump())

            flash("Liste de course générée et enregistrée.", "success")
            return redirect(url_for("list_courses.generate"))

        except Exception as e:
            flash(f"Erreur lors de la génération : {e}", "danger")

    # GET ou POST avec erreur → afficher la page
    # return render_template("generate_courses/generate_liste.html", form=form, results=results)
    return render_template("generate_courses/detail.html", results=session_data_out)
