from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from app.database import get_db


def make_debug_blueprint(name: str, crud):
    """
    Génère un blueprint debug complet pour n'importe quel CRUDGeneric.
    name = "livres", "recettes", etc.
    crud = instance CRUDGeneric(Livre) ou CRUDGeneric(Recette)
    """

    bp = Blueprint(f"debug_{name}", __name__, url_prefix=f"/debug/{name}")

    # -------------------------
    # CREATE
    # -------------------------
    @bp.route("", methods=["POST"])
    def create_obj():
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        with get_db() as db:
            try:
                obj = crud.create(db, data)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            return jsonify({"id": getattr(obj, crud.pk.key)}), 201

    # -------------------------
    # LIST
    # -------------------------
    @bp.route("", methods=["GET"])
    def list_objs():
        with get_db() as db:
            objs = crud.get_all(db)
            return jsonify([serialize(o) for o in objs])

    # -------------------------
    # GET
    # -------------------------
    @bp.route("/<int:id_>", methods=["GET"])
    def get_obj(id_):
        with get_db() as db:
            obj = crud.get(db, id_)
            if not obj:
                return jsonify({"error": "Not found"}), 404
            return jsonify(serialize(obj))

    # -------------------------
    # UPDATE
    # -------------------------
    @bp.route("/<int:id_>", methods=["PATCH"])
    def update_obj(id_):
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        with get_db() as db:
            obj = crud.get(db, id_)
            if not obj:
                return jsonify({"error": "Not found"}), 404

            try:
                updated = crud.update(db, obj, data)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            return jsonify(serialize(updated))

    # -------------------------
    # DELETE
    # -------------------------
    @bp.route("/<int:id_>", methods=["DELETE"])
    def delete_obj(id_):
        with get_db() as db:
            result = crud.delete_restricted(db, id_)

            if result is False:
                obj = crud.get(db, id_)
                if not obj:
                    return jsonify({"error": "Not found"}), 404
                return jsonify({"error": "Cannot delete: ON DELETE RESTRICT"}), 409

            return "", 204

    # -------------------------
    # DELETE ALL
    # -------------------------
    @bp.route("", methods=["DELETE"])
    def delete_all_objs():
        with get_db() as db:
            count = crud.delete_all_restricted(db)
            return jsonify({"deleted": count}), 200

    # -------------------------
    # SEARCH BY ID
    # -------------------------
    @bp.route("/search/<int:id_>", methods=["GET"])
    def search_obj(id_):
        with get_db() as db:
            results = crud.search_by_id(db, id_)
            return jsonify([serialize(o) for o in results])

    # -------------------------
    # EXISTS
    # -------------------------
    @bp.route("/exists", methods=["POST"])
    def exists_obj():
        data = request.get_json()
        if not data or "field" not in data or "value" not in data:
            return jsonify({"error": "Missing field or value"}), 400

        with get_db() as db:
            exists = crud.exists(
                db,
                field=data["field"],
                value=data["value"],
                exclude_id=data.get("exclude_id")
            )
            return jsonify({"exists": exists})

    return bp


def serialize(obj):
    """Convertit un modèle SQLAlchemy en dict JSON."""
    return {
        col.name: getattr(obj, col.name)
        for col in obj.__table__.columns
    }
