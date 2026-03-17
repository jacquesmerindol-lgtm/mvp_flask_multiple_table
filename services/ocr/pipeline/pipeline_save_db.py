# services/ocr/pipeline/pipeline_save_db.py

from database import get_db
from crud import recette_crud
from services.ocr.structuration import Recette  # modèle Pydantic


def run_pipeline_save_recettes(structured_items: list[Recette], id_livre_reference: int):
    """
    structured_items : liste d'objets Pydantic Recette (déjà validés)
    id_livre_reference : clé étrangère obligatoire
    """

    saved = []

    with get_db() as db:
        for item in structured_items:

            obj_in = {
                "nom_recette": item.nom_recette,
                "type_recette": "Autres",
                "nombre_personnes": item.nombre_personnes,
                "duree_preparation": item.duree_preparation,
                "duree_cuisson": item.duree_cuisson,
                "duree_repos": item.duree_repos,
                "liste_ingredients": [ing.model_dump() for ing in item.liste_ingredients],
                "instructions": item.instructions,
                "astuce": item.astuce,
                "id_livre_reference": id_livre_reference,
            }

            db_obj = recette_crud.create(db, obj_in)
            saved.append(db_obj)

    return saved
