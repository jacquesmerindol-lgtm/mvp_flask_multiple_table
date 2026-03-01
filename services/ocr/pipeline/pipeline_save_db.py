# services/ocr/pipeline/pipeline_save_db.py

from database import get_db
from crud import recette_crud
from services.ocr.structuration import Recette  # ton modèle Pydantic

def run_pipeline_save_recettes(structured_list, id_livre_reference: int):
    """
    structured_list : liste de dicts (car stockés dans la session)
    id_livre_reference : clé étrangère obligatoire
    """

    saved = []

    with get_db() as db:
        for data in structured_list:

            # Reconstruction Pydantic
            item = Recette(**data)

            obj_in = {
                "nom_recette": item.nom_recette,
                "type_recette": "recette",
                "nombre_personnes": item.nombre_personnes,
                "duree_preparation": item.temps_preparation or 0,
                "duree_cuisson": item.temps_cuisson or 0,
                "duree_repos": item.temps_repos or 0,
                "liste_ingredients": [ing.model_dump() for ing in item.ingredients],
                "instructions": "\n".join(item.etapes) if item.etapes else None,
                "astuce": item.astuces,
                "id_livre_reference": id_livre_reference,
            }

            db_obj = recette_crud.create(db, obj_in)
            saved.append(db_obj)

    return saved
