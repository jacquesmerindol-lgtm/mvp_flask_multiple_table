"""Schémas utilisés par le service list_ingredients.

Ces définitions sont désormais centralisées dans `services.schema`.
"""

from services.schema import Ingredient, RecetteSelection


# Anciennes définitions (commentées pour historique) :
#
# from pydantic import BaseModel
# from typing import List, Optional
#
# class Ingredient(BaseModel):
#     quantite: Optional[str] = ""
#     unite: Optional[str] = ""
#     ingredient: str
#
# class RecetteSelection(BaseModel):
#     id_recette: str
#     nb_recette: int
#     nom_livre: str
#     numero_livre: Optional[str]
#     nom_recette: str
#     type_recette: str
#     liste_ingredients: List[Ingredient]
