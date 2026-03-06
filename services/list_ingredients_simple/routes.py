from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify

from services.list_ingredients_simple.crud import (
    get_recettes_filtered,
    get_recettes_by_ids,
    get_recettes_full_by_ids,
)
from services.list_ingredients_simple.logic import build_recette_map, build_selection_pydantic

ingredients_bp_simple = Blueprint(
    "recettes_ui_simple",
    __name__,
    url_prefix="/ingredients_simple"
)


# ----------------------------------------------------------------------
# PAGE DE SÉLECTION SIMPLE (GET + POST)
# ----------------------------------------------------------------------
@ingredients_bp_simple.route("/select", methods=["GET", "POST"])
def select_ui():

    # ------------------------------------------------------------------
    # POST : sélection simple (ajout sans doublons)
    # ------------------------------------------------------------------
    if request.method == "POST":
        selected_ids = request.form.getlist("selected_recettes")

        if not selected_ids:
            return redirect(url_for("recettes_ui_simple.select_ui"))

        # Récupérer la sélection existante
        current_ids = session.get("liste_recettes_simple", [])

        # Ajouter uniquement les nouveaux IDs (pas de doublons)
        for rid in selected_ids:
            if rid not in current_ids:
                current_ids.append(rid)

        # Sauvegarde
        session["liste_recettes_simple"] = current_ids

        # Rechargement pour affichage
        recettes = get_recettes_by_ids(current_ids)
        recette_map = build_recette_map(recettes)

        return render_template(
            "select_recettes_simple/selection_result.html",
            selected_ids=current_ids,
            recette_map=recette_map,
        )

    # ------------------------------------------------------------------
    # GET : affichage + filtres + persistance
    # ------------------------------------------------------------------
    selected_ids = session.get("liste_recettes_simple", [])

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

    recette_map = {}
    if selected_ids:
        recettes = get_recettes_by_ids(selected_ids)
        recette_map = build_recette_map(recettes)

    return render_template(
        "select_recettes_simple/select.html",
        rows=rows,
        all_periodes=all_periodes,
        all_robots=all_robots,
        all_types=all_types,
        f_periode=f_periode,
        f_robot=f_robot,
        f_nom=f_nom,
        f_type=f_type,
        selected_ids=selected_ids,
        recette_map=recette_map,
    )


# ----------------------------------------------------------------------
# PAGE DE RÉSULTAT (suppression simple)
# ----------------------------------------------------------------------
@ingredients_bp_simple.route("/select/update", methods=["GET", "POST"])
def update_selection():
    selected_ids = session.get("liste_recettes_simple", [])

    # POST : suppression
    if request.method == "POST":
        rid_to_delete = request.form.get("delete")
        if rid_to_delete:
            selected_ids = [rid for rid in selected_ids if rid != rid_to_delete]
            session["liste_recettes_simple"] = selected_ids
            return redirect(url_for("recettes_ui_simple.update_selection"))

    # GET : affichage
    recettes = get_recettes_by_ids(selected_ids)
    recette_map = build_recette_map(recettes)

    return render_template(
        "select_recettes_simple/selection_result.html",
        selected_ids=selected_ids,
        recette_map=recette_map,
    )


# ----------------------------------------------------------------------
# EXPORT POUR LLM (sans nb_recette)
# ----------------------------------------------------------------------
@ingredients_bp_simple.route("/select/export")
def export_for_llm():
    selected_ids = session.get("liste_recettes_simple", [])
    payload = build_selection_pydantic(selected_ids)
    payload_dicts = [item.model_dump() for item in payload]
    return jsonify(payload_dicts)
