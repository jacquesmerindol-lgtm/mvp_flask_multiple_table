import json
from services.list_ingredients_simple.schema import RecetteSelection, Ingredient
from services.list_ingredients_simple.crud import get_recettes_full_by_ids

# services/list_ingredients/utils.py

def build_recette_map(recettes):
    """Construit un dict id → nom_recette."""
    return {
        str(r.id_recette): r.nom_recette
        for r in recettes
    }


def build_selection_pydantic(selected_ids: list[str]):
    """
    Construit une liste de RecetteSelection (Pydantic) à partir
    d'une simple liste d'IDs de recettes.
    """
    if not selected_ids:
        return []

    rows = get_recettes_full_by_ids(selected_ids)
    result = []

    for row in rows:
        rid = str(row.id_recette)

        # Parse JSON ingrédients
        try:
            ingredients_raw = json.loads(row.liste_ingredients)
        except Exception:
            ingredients_raw = []

        ingredients = [Ingredient(**ing) for ing in ingredients_raw]

        result.append(
            RecetteSelection(
                id_recette=rid,
                nom_livre=row.nom_livre,
                numero_livre=row.numero_livre,
                nom_recette=row.nom_recette,
                type_recette=row.type_recette,
                liste_ingredients=ingredients,
            )
        )

    return result

