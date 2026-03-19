from flask import Blueprint, request, render_template, redirect, url_for, flash

from app.database import get_db
from app.crud import livre_crud
from forms.livre_forms import (
    LivreCreateForm,
    LivreUpdateForm,
    LivreDeleteForm,
    LivreSearchForm
)
from sqlalchemy.exc import IntegrityError
livres_bp = Blueprint("livres", __name__, url_prefix="/livres")
from app.models import Livre
from sqlalchemy import asc, desc

from app.config import get_settings

settings = get_settings()

@livres_bp.route("/", methods=["GET"])
def index():
    form_search = LivreSearchForm(request.args)

    sort = request.args.get("sort", "id_livre")
    order = request.args.get("order", "asc")

    # Whitelist de tri (optionnel mais recommandé)
    allowed_sort = {"id_livre", "nom_livre", "numero_livre", "periode_recettes", "nom_robot"}
    if sort not in allowed_sort:
        sort = "id_livre"


    with get_db() as db:
        query = db.query(Livre)

        # --- Filtrage simple ---
        if form_search.id_livre.data:
            query = query.filter(Livre.id_livre == form_search.id_livre.data)

        if form_search.nom_livre.data:
            query = query.filter(Livre.nom_livre.ilike(f"%{form_search.nom_livre.data}%"))

        if form_search.numero_livre.data:
            query = query.filter(Livre.numero_livre.ilike(f"%{form_search.numero_livre.data}%"))

        # --- Filtre Robot ---
        if form_search.nom_robot.data and form_search.nom_robot.data != "Tous":
            query = query.filter(Livre.nom_robot == form_search.nom_robot.data)

        # --- Filtre Période (JSON list[str]) ---
        if form_search.periode_recettes.data and form_search.periode_recettes.data != "Toutes":
            periode = form_search.periode_recettes.data 
            # On cherche "periode" comme élément dans la liste JSON : "periode"
            query = query.filter(
                Livre.periode_recettes.like(f'%"{periode}"%')
            )

        # --- Tri dynamique ---
        column = getattr(Livre, sort, Livre.id_livre)
        query = query.order_by(desc(column) if order == "desc" else asc(column))

        livres = query.all()

    # Remplissage des listes
    form_search.nom_robot.choices = [("Tous", "Tous")] + [
        (r, r) for r in settings.ROBOTS_LIST
    ]

    form_search.periode_recettes.choices = [("Toutes", "Toutes")] + [
        (p, p) for p in settings.PERIODES_LIST
    ]

    form_delete = LivreDeleteForm()

    return render_template(
        "livres/index.html",
        livres=livres,
        form_search=form_search,
        form_delete=form_delete
    )


@livres_bp.route("/create", methods=["GET", "POST"])
def create():
    form = LivreCreateForm()

    if form.validate_on_submit():
        data = {
            "nom_livre": form.nom_livre.data,
            "numero_livre": form.numero_livre.data or None,
            "periode_recettes": form.periode_recettes.data,
            "nom_robot": form.nom_robot.data
        }

        with get_db() as db:
            try:
                livre_crud.create(db, data)
                flash("Livre créé avec succès.", "success")
                return redirect(url_for("livres.index"))

            except IntegrityError:
                db.rollback()
                form.nom_livre.errors.append("Ce nom existe déjà dans la base.")
                # Pas de redirect → on réaffiche le formulaire avec l’erreur

    return render_template("livres/create.html", form=form)


@livres_bp.route("/<int:id_livre>", methods=["GET"])
def detail(id_livre):
    with get_db() as db:
        livre = livre_crud.get(db, id_livre)
        if not livre:
            flash("Livre non trouvé.", "danger")
            return redirect(url_for("livres.index"))

        form_edit = LivreUpdateForm(obj=livre)
        form_delete = LivreDeleteForm()

        return render_template(
            "livres/detail.html",
            livre=livre,
            form_edit=form_edit,
            form_delete=form_delete
        )

@livres_bp.route("/<int:id_livre>/update", methods=["GET", "POST"])
def update_ui(id_livre):
    with get_db() as db:
        livre = livre_crud.get(db, id_livre)
        if not livre:
            flash("Livre non trouvé.", "danger")
            return redirect(url_for("livres.index"))

        # Pré-remplissage du formulaire
        form = LivreUpdateForm(obj=livre)

        if form.validate_on_submit():
            data = {
                "nom_livre": form.nom_livre.data,
                "numero_livre": form.numero_livre.data or None,
                "periode_recettes": form.periode_recettes.data or [],
                "nom_robot": form.nom_robot.data or None
            }

            try:
                livre_crud.update(db, livre, data)
                flash("Livre mis à jour.", "success")
                return redirect(url_for("livres.detail", id_livre=id_livre))

            except IntegrityError:
                db.rollback()
                # Ajout de l’erreur directement dans le champ
                form.nom_livre.errors.append("Ce nom existe déjà dans la base.")

        # GET ou validation échouée → réaffichage du formulaire avec erreurs
        return render_template("livres/edit.html", form=form, livre=livre)


@livres_bp.route("/<int:id_livre>/delete", methods=["POST"])
def delete_ui(id_livre):
    # form = LivreDeleteForm()

    # if form.validate_on_submit():
    with get_db() as db:
        if not livre_crud.delete_restricted(db, id_livre):
            flash("Impossible de supprimer ce livre.", "danger")
        else:
            flash("Livre supprimé.", "info")

    return redirect(url_for("livres.index"))

@livres_bp.route("/<int:id_livre>/up")
def move_up(id_livre):
    with get_db() as db:
        livre = livre_crud.get(db, id_livre)
        livre.position -= 1
        db.commit()
    return redirect(url_for("livres.index"))


@livres_bp.route("/<int:id_livre>/down")
def move_down(id_livre):
    with get_db() as db:
        livre = livre_crud.get(db, id_livre)
        livre.position += 1
        db.commit()
    return redirect(url_for("livres.index"))
