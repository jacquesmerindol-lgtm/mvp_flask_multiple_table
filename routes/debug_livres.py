from flask import Blueprint, request, jsonify

from app.database import get_db
from app.crud import livre_crud

debug_livres_bp = Blueprint("debug_livres", __name__, url_prefix="/debug/livres")


@debug_livres_bp.route("", methods=["POST"])
def create_livre():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    with get_db() as db:
        livre = livre_crud.create(db, data)
        return jsonify({"id": livre.id_livre}), 201


@debug_livres_bp.route("", methods=["GET"])
def list_livres():
    with get_db() as db:
        livres = livre_crud.get_all(db)
        return jsonify([
            {
                "id_livre": l.id_livre,
                "nom_livre": l.nom_livre,
                "numero_livre": l.numero_livre,
                "periode_recettes": l.periode_recettes,
                "nom_robot": l.nom_robot
            }
            for l in livres
        ])


@debug_livres_bp.route("/<int:id_livre>", methods=["GET"])
def get_livre(id_livre):
    with get_db() as db:
        livre = livre_crud.get(db, id_livre)
        if not livre:
            return jsonify({"error": "Not found"}), 404

        return jsonify({
            "id_livre": livre.id_livre,
            "nom_livre": livre.nom_livre,
            "numero_livre": livre.numero_livre,
            "periode_recettes": livre.periode_recettes,
            "nom_robot": livre.nom_robot
        })


@debug_livres_bp.route("/<int:id_livre>", methods=["PATCH"])
def update_livre(id_livre):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    with get_db() as db:
        livre = livre_crud.get(db, id_livre)
        if not livre:
            return jsonify({"error": "Not found"}), 404

        updated = livre_crud.update(db, livre, data)
        return jsonify({
            "id_livre": updated.id_livre,
            "nom_livre": updated.nom_livre,
            "numero_livre": updated.numero_livre,
            "periode_recettes": updated.periode_recettes,
            "nom_robot": updated.nom_robot
        })


@debug_livres_bp.route("/<int:id_livre>", methods=["DELETE"])
def delete_livre(id_livre):
    with get_db() as db:
        result = livre_crud.delete_restricted(db, id_livre)

        if result is False:
            # Soit not found, soit ON DELETE RESTRICT
            livre = livre_crud.get(db, id_livre)
            if not livre:
                return jsonify({"error": "Not found"}), 404
            return jsonify({"error": "Cannot delete: Livre has Recettes (ON DELETE RESTRICT)"}), 409

        return "", 204


@debug_livres_bp.route("", methods=["DELETE"])
def delete_all_livres():
    with get_db() as db:
        count = livre_crud.delete_all_restricted(db)
        return jsonify({"deleted": count}), 200
    

@debug_livres_bp.route("/search/<int:id_livre>", methods=["GET"])
def search_livre(id_livre):
    with get_db() as db:
        results = livre_crud.search_by_id(db, id_livre)
        return jsonify([
            {
                "id_livre": l.id_livre,
                "nom_livre": l.nom_livre,
                "numero_livre": l.numero_livre,
                "periode_recettes": l.periode_recettes,
                "nom_robot": l.nom_robot
            }
            for l in results
        ])

@debug_livres_bp.route("/exists", methods=["POST"])
def exists_livre():
    data = request.get_json()
    if not data or "field" not in data or "value" not in data:
        return jsonify({"error": "Missing field or value"}), 400

    with get_db() as db:
        exists = livre_crud.exists(
            db,
            field=data["field"],
            value=data["value"],
            exclude_id=data.get("exclude_id")
        )
        return jsonify({"exists": exists})
