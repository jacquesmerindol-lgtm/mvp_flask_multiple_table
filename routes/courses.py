from flask import Blueprint, request, render_template, redirect, url_for, flash

from database import get_db
from crud import course_crud    

from forms.course_form import (
    CourseCreateForm,
    CourseUpdateForm,
    CourseDeleteForm,
    CourseSearchForm
)

from sqlalchemy.exc import IntegrityError

from models import Course
from sqlalchemy import asc, desc

from config import get_settings

from datetime import date
import json

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")

settings = get_settings()

@courses_bp.route("/", methods=["GET"])
def index():
    form_search = CourseSearchForm(request.args)

    sort = request.args.get("sort", "id_course")
    order = request.args.get("order", "asc")

    # Whitelist de tri (optionnel mais recommandé)
    allowed_sort = {"id_course", "date_liste_course"}
    if sort not in allowed_sort:
        sort = "id_course"

    with get_db() as db:
        query = db.query(Course)

        # --- Filtrage simple ---
        if form_search.id_course.data:
            query = query.filter(Course.id_course == form_search.id_course.data)

        if form_search.date_liste_course.data:
            query = query.filter(Course.date_liste_course == form_search.date_liste_course.data)

        # --- Tri dynamique ---
        column = getattr(Course, sort, Course.id_course)
        query = query.order_by(desc(column) if order == "desc" else asc(column))

        courses = query.all()

    form_delete = CourseDeleteForm()

    return render_template(
        "courses/index.html",
        courses=courses,
        form_search=form_search,
        form_delete=form_delete
    )   

@courses_bp.route("/create", methods=["GET", "POST"])
def create():
    form = CourseCreateForm()

    if form.validate_on_submit():    
        # textfield envoit une list mais dans une string (WTForms est un textfield), il faut remplacer les ' dans python par des " dans JSON pour appler le json.loads et avoir une liste dans SQLAlchemy
        # --- Parsing JSON sécurisé ---
        try :
            liste_recette_raw = form.liste_recette.data or []
            liste_recette_list = json.loads(liste_recette_raw.replace("'", '"'))
        except json.JSONDecodeError: 
            flash("Les champs doivent contenir du JSON valide.", "danger")
            return render_template("courses/create.html", form=form)
        
        data = {
            "date_liste_course": form.date_liste_course.data or date.today(),
            "liste_recette": liste_recette_list, #envoyer une liste pour SQLAlchemy 
            "liste_course": form.liste_course.data or None
        }

        with get_db() as db:
            try:
                course_crud.create(db, data)
                flash("Liste de course créée avec succès.", "success")
                return redirect(url_for("courses.index"))

            except IntegrityError:
                db.rollback()
                flash("Erreur lors de la création de la liste de course.", "danger")
                # Pas de redirect → on réaffiche le formulaire avec l’erreur    
                
    return render_template("courses/create.html", form=form)

@courses_bp.route("/<int:id_course>", methods=["GET"])
def detail(id_course):
    with get_db() as db:
        course = course_crud.get(db, id_course)
        if not course:
            flash("Liste de course non trouvée.", "danger")
            return redirect(url_for("course.index"))

        form_edit = CourseUpdateForm(obj=course)
        form_delete = CourseDeleteForm()        
        return render_template(
            "courses/detail.html",
            course=course,
            form_edit=form_edit,
            form_delete=form_delete
            )
    
@courses_bp.route("/<int:id_course>/update", methods=["GET", "POST"])
def update_ui(id_course):   

    with get_db() as db:
        course = course_crud.get(db, id_course)
        form = CourseUpdateForm(obj=course)

        if form.validate_on_submit():
            # textfield envoit une list mais dans une string, il faut remplacer les ' dans python par des " dans JSON   
                    # textfield envoit une list mais dans une string (WTForms est un textfield), il faut remplacer les ' dans python par des " dans JSON pour appler le json.loads et avoir une liste dans SQLAlchemy
            # --- Parsing JSON sécurisé ---
            try :
                liste_recette_raw = form.liste_recette.data or []
                liste_recette_list = json.loads(liste_recette_raw.replace("'", '"'))
            except json.JSONDecodeError: 
                flash("Les champs doivent contenir du JSON valide.", "danger")
                return render_template("courses/edit.html", form=form, course=course)
            
            data = {
                "date_liste_course": form.date_liste_course.data or date.today(),
                "liste_recette": liste_recette_list, #envoyer une liste pour SQLAlchemy 
                "liste_course": form.liste_course.data or None
            }
            try:
                course_crud.update(db, course, data)
                flash("Liste de course mise à jour.", "success")
                return redirect(url_for("courses.detail", id_course=id_course))

            except IntegrityError:
                db.rollback()
                flash("Erreur lors de la création de la liste de course.", "danger")
                # Pas de redirect → on réaffiche le formulaire avec l’erreur    
    return render_template("courses/edit.html", form=form, course=course)

@courses_bp.route("/<int:id_course>/delete", methods=["POST"])
def delete_ui(id_course):
    with get_db() as db:
        if not course_crud.delete_restricted(db, id_course):
            flash("Impossible de supprimer cette liste de course.", "danger")
        else:
            flash("Liste de course supprimée.", "info")

    return redirect(url_for("courses.index"))   

@courses_bp.route("/<int:id_course>/up")
def move_up(id_course):     
    with get_db() as db:
        course = course_crud.get(db, id_course)
        course.position -= 1
        db.commit()
    return redirect(url_for("courses.index"))

@courses_bp.route("/<int:id_course>/down")
def move_down(id_course):
    with get_db() as db:
        course = course_crud.get(db, id_course) 
        course.position += 1
        db.commit()
    return redirect(url_for("courses.index"))   





        




