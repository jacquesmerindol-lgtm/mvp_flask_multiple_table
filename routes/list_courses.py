from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import get_db

from services.list_course.pipeline import pipeline_liste_course
from services.list_course.redis_store import (
    get_list_course_output,
    get_list_course_selection,
)
from app.crud import course_crud
from services.schema import ListeCourse

list_course_bp = Blueprint("list_courses", __name__, url_prefix="/list_courses")


@list_course_bp.route("/generate", methods=["GET", "POST"])
def generate():
    user_id = request.cookies.get("user_id")
    selected_data_pydantic = get_list_course_selection(user_id)

    if request.method == "POST":
        if not selected_data_pydantic.recette_selection_items:
            flash("Aucune liste disponible. Veuillez sélectionner des recettes.", "warning")
            return redirect(url_for("recettes.index"))

        try:
            results: ListeCourse = pipeline_liste_course(selected_data_pydantic)

            with get_db() as db:
                course_crud.create(db, results.model_dump())

            flash("Liste de course générée et enregistrée.", "success")
            return redirect(url_for("list_courses.generate"))

        except Exception as e:
            flash(f"Erreur lors de la génération : {e}", "danger")

    results = get_list_course_output(user_id)

    return render_template(
        "generate_courses/detail.html",
        results=results,
    )
