from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


# ======================
# MODÈLES PYDANTIC
# ======================

# --- Modèle minimal : utilisé dans /select ---
class RecetteQuantifiee(BaseModel):
    id_recette: str
    nb_recette: int


class ListeRecetteQuantifiee(BaseModel):
    items: list[RecetteQuantifiee]

# --- Modèle enrichi : utilisé dans /update et /generate ---
class Ingredient(BaseModel):
    quantite: str =""
    unite: str =""
    ingredient: str

class RecetteSelection(BaseModel):
    id_recette: str
    nb_recette: int
    nom_livre: str
    numero_livre: str =""
    nom_recette: str
    type_recette: str
    liste_ingredients: list[Ingredient]

class ListeRecetteSelection(BaseModel):
    recette_selection_items: List[RecetteSelection]

class ListeCourse(BaseModel):
    date_liste_course: datetime = Field(description="Date de la liste des courses")
    liste_recette: list[RecetteSelection] = Field(description="Liste des recettes associées")
    liste_course: str = Field(description="Liste des courses formatée")
