from app.database import get_db
from app.models import Livre, Recette

def get_recettes_filtered(
    periode: str | None = None,
    robot: str | None = None,
    nom_recette: str | None = None,
    type_recette: str | None = None,
):
    with get_db() as db:
        q = (
            db.query(
                Livre.nom_livre,
                Livre.numero_livre,
                Livre.periode_recettes,
                Livre.nom_robot,
                Recette.id_recette,
                Recette.position,
                Recette.nom_recette,
                Recette.type_recette,
                Recette.nombre_personnes,
                Recette.duree_preparation,
                Recette.duree_cuisson,
                Recette.duree_repos,
                Recette.liste_ingredients,
                Recette.instructions,
                Recette.astuce,
                Recette.id_livre_reference,
            )
            .join(Livre, Recette.id_livre_reference == Livre.id_livre)
            .order_by(Livre.nom_livre, Recette.nom_recette)
        )

        if periode:
            # q = q.filter(Livre.periode_recettes.contains([periode]))
            q = q.filter(Livre.periode_recettes.contains(periode))
        if robot:
            q = q.filter(Livre.nom_robot == robot)
        if nom_recette:
            q = q.filter(Recette.nom_recette.ilike(f"%{nom_recette}%"))
        if type_recette:
            q = q.filter(Recette.type_recette == type_recette)

        return q.all()


def get_recettes_by_ids(ids: list[str]):
    if not ids:
        return []

    with get_db() as db:
        return (
            db.query(Recette)
            .filter(Recette.id_recette.in_(ids))
            .all()
        )


def get_recettes_full_by_ids(ids: list[str]):
    if not ids:
        return []

    with get_db() as db:
        return (
            db.query(
                Recette.id_recette,
                Recette.nom_recette,
                Recette.type_recette,
                Recette.liste_ingredients,
                Livre.nom_livre,
                Livre.numero_livre,
            )
            .join(Livre, Recette.id_livre_reference == Livre.id_livre)
            .filter(Recette.id_recette.in_(ids))
            .all()
        )
