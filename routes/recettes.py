from flask import Blueprint, request, render_template, redirect, url_for, flash

from database import get_db
from crud import recette_crud, livre_crud
from forms.recette_forms import (
    RecetteCreateForm,
    RecetteUpdateForm,
    RecetteDeleteForm,
    RecetteSearchForm
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc, desc
from models import Recette

from config import get_settings
settings = get_settings()



recettes_bp = Blueprint("recettes", __name__, url_prefix="/recettes")


# @recettes_bp.route("/", methods=["GET"])
# def index():
#     form_search = RecetteSearchForm(request.args)

#     with get_db() as db:
#         if form_search.id_recette.data:
#             recettes = recette_crud.search_by_id(db, form_search.id_recette.data)
#         else:
#             recettes = recette_crud.get_all(db)

#         livres = livre_crud.get_all(db)

#     # Pour affichage dans le tableau
#     livres_dict = {
#         l.id_livre: f"{l.numero_livre or 'N/A'} — {l.nom_livre}"
#         for l in livres
#     }

#     form_delete = RecetteDeleteForm()

#     return render_template(
#         "recettes/index.html",
#         recettes=recettes,
#         livres=livres_dict,
#         form_search=form_search,
#         form_delete=form_delete
#     )

# @recettes_bp.route("/", methods=["GET"])
# def index():
#     form_search = RecetteSearchForm(request.args)

#     # Lecture des paramètres de tri
#     sort = request.args.get("sort", "id_recette")
#     order = request.args.get("order", "asc")

#     with get_db() as db:
#         # Base de la requête
#         query = db.query(Recette)
#         query = query.order_by(Recette.position.asc())


#         # Recherche par ID
#         if form_search.id_recette.data:
#             query = query.filter(Recette.id_recette == form_search.id_recette.data)

#         # Tri dynamique sécurisé
#         column = getattr(Recette, sort, Recette.id_recette)

#         if order == "desc":
#             query = query.order_by(desc(column))
#         else:
#             query = query.order_by(asc(column))

#         recettes = query.all()

#         # Chargement des livres pour affichage
#         livres = livre_crud.get_all(db)
#         livres_dict = {
#             l.id_livre: f"{l.numero_livre or 'N/A'} — {l.nom_livre}"
#             for l in livres
#         }

#     form_delete = RecetteDeleteForm()

#     return render_template(
#         "recettes/index.html",
#         recettes=recettes,
#         livres=livres_dict,
#         form_search=form_search,
#         form_delete=form_delete
#     )

# @recettes_bp.route("/", methods=["GET"])
# def index():
#     form_search = RecetteSearchForm(request.args)

#     # Lecture des paramètres de tri
#     sort = request.args.get("sort", "id_recette")
#     order = request.args.get("order", "asc")

#     with get_db() as db:
#         # Base de la requête
#         query = db.query(Recette)

#         # Recherche
#         if form_search.id_recette.data:
#             query = query.filter(Recette.id_recette == form_search.id_recette.data)


#         # --- Filtrage multi-champs ---
#         if form_search.nom_recette.data:
#             query = query.filter(
#                 Recette.nom_recette.ilike(f"%{form_search.nom_recette.data}%")
#             )

#         if form_search.type_recette.data:
#             query = query.filter(
#                 Recette.type_recette == form_search.type_recette.data
#             )

#         if form_search.nombre_personnes.data:
#             query = query.filter(
#                 Recette.nombre_personnes == form_search.nombre_personnes.data
#             )

#         if form_search.id_livre_reference.data and form_search.id_livre_reference.data != 0:
#             query = query.filter(
#                 Recette.id_livre_reference == form_search.id_livre_reference.data
#             )

#         # --- Tri dynamique ---
#         column = getattr(Recette, sort, Recette.id_recette) 
#         query = query.order_by(
#             desc(column) if order == "desc" else asc(column)
#         )

#         recettes = query.all()

#         # Chargement des livres pour affichage
#         livres = livre_crud.get_all(db)
#         livres_dict = {
#             l.id_livre: f"{l.numero_livre or 'N/A'} — {l.nom_livre}"
#             for l in livres
#         }

#         # Remplissage du select Livre
#         form_search.id_livre_reference.choices = [(0, "Tous")] + [
#             (l.id_livre, f"{l.numero_livre or 'N/A'} — {l.nom_livre}") for l in livres
#         ]


#     form_delete = RecetteDeleteForm()

#     return render_template(
#         "recettes/index.html",
#         recettes=recettes,
#         livres=livres_dict,
#         form_search=form_search,
#         form_delete=form_delete
#     )

@recettes_bp.route("/", methods=["GET"])
def index():
    form_search = RecetteSearchForm(request.args)
    form_delete = RecetteDeleteForm()

    sort = request.args.get("sort", "id_recette")
    order = request.args.get("order", "asc")

    with get_db() as db:
        query = db.query(Recette)

        if form_search.id_recette.data:
            query = query.filter(Recette.id_recette == form_search.id_recette.data)

        if form_search.nom_recette.data:
            query = query.filter(
                Recette.nom_recette.ilike(f"%{form_search.nom_recette.data}%")
            )

        if form_search.type_recette.data:
            query = query.filter(
                Recette.type_recette == form_search.type_recette.data
            )

        if form_search.nombre_personnes.data:
            query = query.filter(
                Recette.nombre_personnes == form_search.nombre_personnes.data
            )

        if form_search.id_livre_reference.data and form_search.id_livre_reference.data != 0:
            query = query.filter(
                Recette.id_livre_reference == form_search.id_livre_reference.data
            )

        column = getattr(Recette, sort, Recette.id_recette)
        query = query.order_by(desc(column) if order == "desc" else asc(column))

        recettes = query.all()

        # --- Livres pour le select ---
        livres = livre_crud.get_all(db)
        form_search.id_livre_reference.choices = [(0, "Tous")] + [
            (l.id_livre, f"{l.numero_livre or 'N/A'} — {l.nom_livre}") for l in livres
        ]

        # --- 🔥 Livres pour affichage dans le tableau ---
        livres_dict = {
            l.id_livre: f"{l.numero_livre or 'N/A'} — {l.nom_livre}"
            for l in livres
        }

    # --- Types de recette depuis config ---
    form_search.type_recette.choices = [("", "Tous")] + [
        (t, t) for t in settings.RECETTE_TYPES
    ]

    return render_template(
        "recettes/index.html",
        recettes=recettes,
        form_search=form_search,
        form_delete=form_delete,
        livres=livres_dict   # 🔥 maintenant défini
    )



@recettes_bp.route("/create", methods=["GET", "POST"])
def create():
    form = RecetteCreateForm()

    if form.validate_on_submit():
        data = {
            "nom_recette": form.nom_recette.data,
            "type_recette": form.type_recette.data,
            "nombre_personnes": form.nombre_personnes.data,
            "duree_preparation": form.duree_preparation.data or 0,
            "duree_cuisson": form.duree_cuisson.data or 0,
            "duree_repos": form.duree_repos.data or 0,
            "liste_ingredients": form.liste_ingredients.data or [],
            "instructions": form.instructions.data or None,
            "astuce": form.astuce.data or None,
            "id_livre_reference": form.id_livre_reference.data
        }

        with get_db() as db:
            try:
                recette_crud.create(db, data)
                flash("Recette créée avec succès.", "success")
                return redirect(url_for("recettes.index"))

            except IntegrityError:
                db.rollback()
                # Ajout de l’erreur directement dans le champ concerné
                form.nom_recette.errors.append("Ce nom existe déjà dans la base.")

    # GET ou validation échouée → réaffichage du formulaire avec erreurs
    return render_template("recettes/create.html", form=form)




@recettes_bp.route("/<int:id_recette>", methods=["GET"])
def detail(id_recette):
    with get_db() as db:
        recette = recette_crud.get(db, id_recette)
        if not recette:
            flash("Recette non trouvée.", "danger")
            return redirect(url_for("recettes.index"))

        livre = livre_crud.get(db, recette.id_livre_reference)

    form_edit = RecetteUpdateForm(obj=recette)
    form_delete = RecetteDeleteForm()

    return render_template(
        "recettes/detail.html",
        recette=recette,
        livre=livre,
        form_edit=form_edit,
        form_delete=form_delete
    )


@recettes_bp.route("/<int:id_recette>/update", methods=["GET", "POST"])
def update_ui(id_recette):

    with get_db() as db:
        recette = recette_crud.get(db, id_recette)
        if not recette:
            flash("Recette non trouvée.", "danger")
            return redirect(url_for("recettes.index"))

        # Pré-remplissage du formulaire avec l'objet existant
        form = RecetteUpdateForm(obj=recette)

        if form.validate_on_submit():
            data = {
                "nom_recette": form.nom_recette.data,
                "type_recette": form.type_recette.data,
                "nombre_personnes": form.nombre_personnes.data,
                "duree_preparation": form.duree_preparation.data or 0,
                "duree_cuisson": form.duree_cuisson.data or 0,
                "duree_repos": form.duree_repos.data or 0,
                "liste_ingredients": form.liste_ingredients.data or [],
                "instructions": form.instructions.data or None,
                "astuce": form.astuce.data or None,
                "id_livre_reference": form.id_livre_reference.data
            }

            try:
                recette_crud.update(db, recette, data)
                flash("Recette mise à jour.", "success")
                return redirect(url_for("recettes.detail", id_recette=id_recette))

            except IntegrityError:
                db.rollback()
                # Ajout de l’erreur directement dans le champ concerné
                form.nom_recette.errors.append("Ce nom existe déjà dans la base.")

    # GET ou validation échouée → réaffichage du formulaire avec erreurs
    return render_template("recettes/edit.html", form=form, recette=recette)



@recettes_bp.route("/<int:id_recette>/delete", methods=["POST"])
def delete_ui(id_recette):
    # form = RecetteDeleteForm()

    # if form.validate_on_submit():
    with get_db() as db:
        if not recette_crud.delete_restricted(db, id_recette):
            flash("Impossible de supprimer cette recette.", "danger")
        else:
            flash("Recette supprimée.", "info")

    return redirect(url_for("recettes.index"))

@recettes_bp.route("/<int:id_recette>/up")
def move_up(id_recette):
    with get_db() as db:
        recette = recette_crud.get(db, id_recette)
        recette.position -= 1
        db.commit()
    return redirect(url_for("recettes.index"))

@recettes_bp.route("/<int:id_recette>/down")
def move_down(id_recette):
    with get_db() as db:
        recette = recette_crud.get(db, id_recette)
        recette.position += 1
        db.commit()
    return redirect(url_for("recettes.index"))