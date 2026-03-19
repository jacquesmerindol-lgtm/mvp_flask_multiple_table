from flask import Blueprint, request, render_template, redirect, url_for, flash

from app.database import get_db
from app.models import Entity
from app.crud import entity_crud
from forms.entity_forms import (
    EntityCreateForm,
    EntityUpdateForm,
    EntityDeleteForm,
    EntitySearchForm,
)
from sqlalchemy import asc, desc

entity_bp = Blueprint("entity", __name__, url_prefix="/entity")


@entity_bp.route("/", methods=["GET"])
def index():
    form_search = EntitySearchForm(request.args)
    form_delete = EntityDeleteForm()

    sort = request.args.get("sort", "id_entity")
    order = request.args.get("order", "asc")

    allowed_sort = {"id_entity", "champ1", "champ2"}
    if sort not in allowed_sort:
        sort = "id_entity"

    with get_db() as db:
        query = db.query(Entity)

        if form_search.id_entity.data:
            query = query.filter(Entity.id_entity == form_search.id_entity.data)

        if form_search.champ1.data:
            query = query.filter(Entity.champ1.ilike(f"%{form_search.champ1.data}%"))

        column = getattr(Entity, sort, Entity.id_entity)
        query = query.order_by(desc(column) if order == "desc" else asc(column))

        items = query.all()

    return render_template(
        "entity/index.html",
        items=items,
        form_search=form_search,
        form_delete=form_delete,
    )


@entity_bp.route("/create", methods=["GET", "POST"])
def create():
    form = EntityCreateForm()

    if form.validate_on_submit():
        data = {
            "champ1": form.champ1.data,
            "champ2": form.champ2.data,
        }

        with get_db() as db:
            entity_crud.create(db, data)
            flash("Entity créé avec succès.", "success")
            return redirect(url_for("entity.index"))

    return render_template("entity/create.html", form=form)


@entity_bp.route("/<int:id_entity>", methods=["GET"])
def detail(id_entity):
    with get_db() as db:
        item = entity_crud.get(db, id_entity)

    form_edit = EntityUpdateForm(obj=item)
    form_delete = EntityDeleteForm()

    return render_template(
        "entity/detail.html",
        item=item,
        form_edit=form_edit,
        form_delete=form_delete,
    )


@entity_bp.route("/<int:id_entity>/update", methods=["POST"])
def update_ui(id_entity):
    with get_db() as db:
        item = entity_crud.get(db, id_entity)

        form = EntityUpdateForm()

        if form.validate_on_submit():
            data = {
                "champ1": form.champ1.data,
                "champ2": form.champ2.data,
            }

            entity_crud.update(db, item, data)
            flash("Entity mis à jour.", "success")
            return redirect(url_for("entity.detail", id_entity=id_entity))

    return render_template("entity/edit.html", form=form, item=item)


@entity_bp.route("/<int:id_entity>/delete", methods=["POST"])
def delete_ui(id_entity):
    with get_db() as db:
        entity_crud.delete(db, id_entity)
        flash("Entity supprimé.", "info")

    return redirect(url_for("entity.index"))
