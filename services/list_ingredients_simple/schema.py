from pydantic import BaseModel
from typing import List, Optional

class Ingredient(BaseModel):
    quantite: Optional[str]
    unite: Optional[str]
    ingredient: str

class RecetteSelection(BaseModel):
    id_recette: str
    nom_livre: str
    numero_livre: Optional[str]
    nom_recette: str
    type_recette: str
    liste_ingredients: List[Ingredient]
