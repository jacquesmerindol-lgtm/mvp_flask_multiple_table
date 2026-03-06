from flask import Blueprint, render_template, request, session, redirect, url_for

from services.list_ingredients.crud import (
    get_recettes_filtered,
    get_recettes_by_ids,
)
from services.list_ingredients.logic import build_recette_map

import json


ingredients_bp = Blueprint("recettes_ui", __name__, url_prefix="/ingredients")


@ingredients_bp.route("/select", methods=["GET", "POST"])
def select_ui():

    # ----------------------------------------------------------------------
    # POST : ajout de recettes à la sélection (avec addition des quantités)
    # ----------------------------------------------------------------------
    if request.method == "POST":
        selected_ids = request.form.getlist("selected_recettes")

        # Si aucune case cochée → ne rien modifier
        if not selected_ids:
            return redirect(url_for("recettes_ui.select_ui"))

        # On part de la sélection existante
        selected_data = session.get("liste_recettes", {}).copy()

        # Ajout / addition des quantités
        for rid in selected_ids:
            nb_new = int(request.form.get(f"nb_recette_{rid}", 1))

            if rid in selected_data:
                selected_data[rid]["nb_recette"] += nb_new
            else:
                selected_data[rid] = {"nb_recette": nb_new}

        # Sauvegarde
        session["liste_recettes"] = selected_data

        # Rechargement des recettes pour affichage
        recettes = get_recettes_by_ids(list(selected_data.keys()))
        recette_map = build_recette_map(recettes)

        return render_template(
            "select_recettes/selection_result.html",
            selected_data=selected_data,
            recette_map=recette_map,
        )

    # ----------------------------------------------------------------------
    # GET : affichage + filtres + persistance de la sélection
    # ----------------------------------------------------------------------
    selected_data = session.get("liste_recettes", {})

    f_periode = request.args.get("periode")
    f_robot = request.args.get("robot")
    f_nom = request.args.get("nom")
    f_type = request.args.get("type")

    rows = get_recettes_filtered(
        periode=f_periode,
        robot=f_robot,
        nom_recette=f_nom,
        type_recette=f_type,
    )


    all_periodes = sorted({p for r in rows for p in r.periode_recettes})
    all_robots = sorted({r.nom_robot for r in rows})
    all_types = sorted({r.type_recette for r in rows})

    # 🔥 Construire un map lisible pour la sélection existante
    recette_map = {}
    if selected_data:
        ids = list(selected_data.keys())
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
        selected_data=selected_data,
        recette_map=recette_map,
        
    )


# ----------------------------------------------------------------------
# PAGE DE MISE À JOUR DE LA SÉLECTION
# ----------------------------------------------------------------------
@ingredients_bp.route("/select/update", methods=["GET", "POST"])
def update_selection():
    selected_data = session.get("liste_recettes", {})

    # POST : suppression ou modification
    if request.method == "POST":

        # Suppression
        rid_to_delete = request.form.get("delete")
        if rid_to_delete:
            selected_data.pop(rid_to_delete, None)
            session["liste_recettes"] = selected_data
            return redirect(url_for("recettes_ui.update_selection"))

        # Mise à jour des quantités
        for rid in list(selected_data.keys()):
            new_value = request.form.get(f"nb_recette_{rid}")
            if new_value:
                selected_data[rid]["nb_recette"] = int(new_value)

        session["liste_recettes"] = selected_data
        return redirect(url_for("recettes_ui.update_selection"))

    # GET : affichage
    ids = list(selected_data.keys())
    recettes = get_recettes_by_ids(ids)
    recette_map = build_recette_map(recettes)

    return render_template(
        "select_recettes/selection_result.html",
        selected_data=selected_data,
        recette_map=recette_map,
    )


from services.list_ingredients.logic import build_selection_pydantic
from flask import jsonify

@ingredients_bp.route("/select/export")
def export_for_llm():
    selected_data = session.get("liste_recettes", {})
    payload = build_selection_pydantic(selected_data)

    # Convertir en liste de dicts 
    payload_dicts = [item.model_dump() for item in payload] 
    
    return jsonify(payload_dicts)


