from flask import Blueprint, request, jsonify

from database import get_db
from crud import recette_crud

debug_recettes_bp = Blueprint("debug_recettes", __name__, url_prefix="/debug/recettes")


@debug_recettes_bp.route("", methods=["POST"])
def create_recette():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    with get_db() as db:
        recette = recette_crud.create(db, data)
        return jsonify({"id": recette.id_recette}), 201


@debug_recettes_bp.route("", methods=["GET"])
def list_recettes():
    with get_db() as db:
        recettes = recette_crud.get_all(db)
        return jsonify([
            {
                "id_recette": r.id_recette,
                "nom_recette": r.nom_recette,
                "type_recette": r.type_recette,
                "nombre_personnes": r.nombre_personnes,
                "duree_preparation": r.duree_preparation,
                "duree_cuisson": r.duree_cuisson,
                "duree_repos": r.duree_repos,
                "liste_ingredients": r.liste_ingredients,
                "instructions": r.instructions,
                "astuce": r.astuce,
                "id_livre_reference": r.id_livre_reference
            }
            for r in recettes
        ])


@debug_recettes_bp.route("/<int:id_recette>", methods=["GET"])
def get_recette(id_recette):
    with get_db() as db:
        recette = recette_crud.get(db, id_recette)
        if not recette:
            return jsonify({"error": "Not found"}), 404

        return jsonify({
            "id_recette": recette.id_recette,
            "nom_recette": recette.nom_recette,
            "type_recette": recette.type_recette,
            "nombre_personnes": recette.nombre_personnes,
            "duree_preparation": recette.duree_preparation,
            "duree_cuisson": recette.duree_cuisson,
            "duree_repos": recette.duree_repos,
            "liste_ingredients": recette.liste_ingredients,
            "instructions": recette.instructions,
            "astuce": recette.astuce,
            "id_livre_reference": recette.id_livre_reference
        })


@debug_recettes_bp.route("/<int:id_recette>", methods=["PATCH"])
def update_recette(id_recette):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    with get_db() as db:
        recette = recette_crud.get(db, id_recette)
        if not recette:
            return jsonify({"error": "Not found"}), 404

        updated = recette_crud.update(db, recette, data)
        return jsonify({
            "id_recette": updated.id_recette,
            "nom_recette": updated.nom_recette,
            "type_recette": updated.type_recette,
            "nombre_personnes": updated.nombre_personnes,
            "duree_preparation": updated.duree_preparation,
            "duree_cuisson": updated.duree_cuisson,
            "duree_repos": updated.duree_repos,
            "liste_ingredients": updated.liste_ingredients,
            "instructions": updated.instructions,
            "astuce": updated.astuce,
            "id_livre_reference": updated.id_livre_reference
        })


@debug_recettes_bp.route("/<int:id_recette>", methods=["DELETE"])
def delete_recette(id_recette):
    with get_db() as db:
        result = recette_crud.delete_restricted(db, id_recette)

        if result is False:
            # Soit not found, soit ON DELETE RESTRICT
            recette = recette_crud.get(db, id_recette)
            if not recette:
                return jsonify({"error": "Not found"}), 404
            return jsonify({"error": "Cannot delete: Livre has Recettes (ON DELETE RESTRICT)"}), 409

        return "", 204


@debug_recettes_bp.route("", methods=["DELETE"])
def delete_all_recettes():
    with get_db() as db:
        count = recette_crud.delete_all_restricted(db)
        return jsonify({"deleted": count}), 200
