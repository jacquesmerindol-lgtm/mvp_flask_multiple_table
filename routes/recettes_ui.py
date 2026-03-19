from flask import Blueprint, render_template, request, redirect, url_for
from services.list_course.crud import get_recettes_filtered, get_recettes_by_ids
from services.list_course.logic import build_selection_pydantic, build_recette_map
from services.schema import Recette, ListeRecetteSelection, RecetteQuantifiee
from services.list_course.redis_store import (
    get_list_course_selection,
    save_list_course_selection,
)


ingredients_bp = Blueprint("recettes_ui", __name__, url_prefix="/ingredients")


@ingredients_bp.route("/select", methods=["GET", "POST"])
def select_ui():
    """Selection de recettes (ajout + quantités)."""

    user_id = request.cookies.get("user_id")

    if request.method == "POST":
        selected_ids: list[str] = request.form.getlist("selected_recettes")

        if not selected_ids:
            return redirect(url_for("recettes_ui.select_ui"))

        enriched = get_list_course_selection(user_id)

        minimal = ListeRecetteSelection(
            items=[
                RecetteQuantifiee(id_recette=item.id_recette, nb_recette=item.nb_recette)
                for item in enriched.recette_selection_items
            ]
        )

        nb_map: dict[str, int] = {
            item.id_recette: item.nb_recette for item in minimal.items
        }

        for rid in selected_ids:
            nb_new: int = int(request.form.get(f"nb_recette_{rid}", 1))
            nb_map[rid] = nb_map.get(rid, 0) + nb_new

        minimal = ListeRecetteSelection(
            items=[
                RecetteQuantifiee(id_recette=k, nb_recette=v)
                for k, v in nb_map.items()
            ]
        )

        enriched = build_selection_pydantic(minimal)
        save_list_course_selection(user_id, enriched)

        ids: list[str] = [item.id_recette for item in enriched.recette_selection_items]
        recettes = get_recettes_by_ids(ids)
        recette_map = build_recette_map(recettes)

        return render_template(
            "select_recettes/selection_result.html",
            selected_data=enriched.recette_selection_items,
            recette_map=recette_map,
        )

    # GET
    enriched = get_list_course_selection(user_id)

    f_periode: str | None = request.args.get("periode")
    f_robot: str | None = request.args.get("robot")
    f_nom: str | None = request.args.get("nom")
    f_type: str | None = request.args.get("type")

    rows = get_recettes_filtered(
        periode=f_periode,
        robot=f_robot,
        nom_recette=f_nom,
        type_recette=f_type,
    )

    all_periodes = sorted({p for r in rows for p in r.periode_recettes})
    all_robots = sorted({r.nom_robot for r in rows})
    all_types = sorted({r.type_recette for r in rows})

    recette_map: dict[str, Recette] = {}
    if enriched:
        ids = [item.id_recette for item in enriched.recette_selection_items]
        recettes = get_recettes_by_ids(ids)
        recette_map = build_recette_map(recettes)

    return render_template(
        "select_recettes/select.html",
        rows=rows,
        all_periodes=all_periodes,
        all_robots=all_robots,
        all_types=all_types,
        f_periode=f_periode,
        f_robot=f_robot,
        f_nom=f_nom,
        f_type=f_type,
        selected_data=enriched.recette_selection_items if enriched else [],
        recette_map=recette_map,
    )


@ingredients_bp.route("/select/update", methods=["GET", "POST"])
def update_selection():
    user_id = request.cookies.get("user_id")
    selected_data_pydantic: ListeRecetteSelection = get_list_course_selection(user_id)

    if request.method == "POST":
        rid_to_delete = request.form.get("delete")
        if rid_to_delete:
            selected_data_pydantic = ListeRecetteSelection(
                recette_selection_items=[
                    item for item in selected_data_pydantic.recette_selection_items
                    if item.id_recette != rid_to_delete
                ]
            )
            save_list_course_selection(user_id, selected_data_pydantic)
            return redirect(url_for("recettes_ui.update_selection"))

        updated_list = []
        for item in selected_data_pydantic.recette_selection_items:
            new_value = request.form.get(f"nb_recette_{item.id_recette}")
            if new_value:
                updated_item = item.model_copy(update={"nb_recette": int(new_value)})
            else:
                updated_item = item
            updated_list.append(updated_item)

        updated_list_pydantic = ListeRecetteSelection(recette_selection_items=updated_list)
        save_list_course_selection(user_id, updated_list_pydantic)

        return redirect(url_for("recettes_ui.update_selection"))

    ids = [item.id_recette for item in selected_data_pydantic.recette_selection_items]
    recettes = get_recettes_by_ids(ids)
    recette_map = build_recette_map(recettes)

    return render_template(
        "select_recettes/selection_result.html",
        selected_data=selected_data_pydantic.recette_selection_items,
        recette_map=recette_map,
    )
