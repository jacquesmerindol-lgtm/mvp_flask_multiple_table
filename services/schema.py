"""Schémas Pydantic partagés pour l'ensemble du projet.

Ce fichier centralise toutes les définitions de modèles Pydantic afin de :
- éviter la duplication des modèles entre différents modules
- faciliter la maintenance
- permettre de commenter les anciennes définitions locales sans les supprimer

Les anciens schémas restent commentés dans leurs fichiers d'origine pour historique.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Type

from pydantic import BaseModel, Field, RootModel


# ======================
# SCHÉMAS LISTE DE COURSES
# ======================

class RecetteQuantifiee(BaseModel):
    id_recette: str
    nb_recette: int


class ListeRecetteQuantifiee(BaseModel):
    items: List[RecetteQuantifiee]


# class Ingredient(BaseModel):
#     quantite: Optional[str] = ""
#     unite: Optional[str] = ""
#     ingredient: str


class RecetteSelection(BaseModel):
    id_recette: str
    nb_recette: int
    nom_livre: str
    numero_livre: Optional[str] = ""
    nom_recette: str
    type_recette: str
    liste_ingredients: List[Ingredient]


class ListeRecetteSelection(BaseModel):
    recette_selection_items: List[RecetteSelection]


class ListeCourse(BaseModel):
    date_liste_course: datetime = Field(description="Date de la liste des courses")
    liste_recette: List[RecetteSelection] = Field(description="Liste des recettes associées")
    liste_course: str = Field(description="Liste des courses formatée")


# ======================
# SCHÉMAS OCR
# ======================

class OCRResult(BaseModel):
    """Représente le résultat OCR d’un seul document (image ou PDF)."""

    image_path: str = ""
    md_data: str = ""
    enhanced_md: str = Field(
        default="",
        description="Markdown amélioré par LLM (optionnel)",
    )


class OCRResults(BaseModel):
    """Conteneur des résultats OCR."""

    ocr_results_items: List[OCRResult] = Field(
        default_factory=list,
        description="Liste des résultats OCR",
    )


# class Ingredient(BaseModel):
#     ingredient: str = Field(description="Nom de l’ingrédient, sans quantité.")
#     quantite: str = Field(description="Quantité associée à l’ingrédient; répond non précisé si aucune quantité n'est mentionnée.")
#     unite : str = Field(description="Unité associée à l’ingrédient; répond par une chaine de caractère vide si aucune unité n'est mentionnée.")


# class Recette(BaseModel):
#     lien_fichier: str = Field(
#         description="Chemin ou nom du fichier source."
#     )

#     nom_recette: str = Field(
#         description="Nom exact de la recette tel qu'indiqué dans le texte."
#     )

#     nombre_personnes: int = Field(
#         description="Nombre de personnes indiqué dans le texte."
#     )

#     duree_preparation: str = Field(
#         description="Durée de préparation indiquée dans le texte."
#     )

#     duree_cuisson: str = Field(
#         description="Durée de cuisson indiquée dans le texte."
#     )

#     duree_repos: str = Field(
#         description="Durée de repos indiquée dans le texte, ou chaîne vide si absente."
#     )

#     liste_ingredients: List[Ingredient] = Field( 
#         description=( 
#             "Liste structurée de tous les ingrédients mentionnés dans la section ingrédients. "
#             "Le champ 'ingredients' doit être une liste d'objets au format Ingredient: {nom, quantite}."
#             "Chaque élément contient un nom d’ingrédient et une quantité séparée."
#             "utilise uniquement les apostrophes typographiques ’ et non les apostrophes internes ' dans les phrases  ")
#     )

#     instructions: List[str] = Field(
#         description="Étapes de préparation générales (section 'LA RECETTE'), en incluant les éléments listés dans la section PRÉPARATION AU ROBOT." )
   
#     etapes_companion: List[str] = Field(
#         description=(
#             "Étapes spécifiques au robot Companion extraites du tableau : "
#             "pour chaque ligne du tableau où la première colonne contient une étape, "
#             "combiner le texte de la première colonne avec l'instruction de la colonne 'Companion'. "
#             "Ignorer les lignes vides mais inclure les lignes d'accessoires. "
#             "Si le tableau ne contient pas de colonne 'Companion', renvoyer ['néant']."
#             "utilise uniquement les apostrophes typographiques ’ et non les apostrophes internes ' dans les phrases "
#         )
#     )

#     astuce: str = Field(
#         description="Conseils ou remarques éventuelles extraits du texte."
#     )    


class Facture(BaseModel):
    lien_fichier: str
    numero_facture: str
    fournisseur: str
    date: str
    montant_total: str
    lignes: List[str]


# Registre global des schémas disponibles (pour sélection dynamique)
SCHEMAS: Dict[str, Type[BaseModel]] = {
    "Recette": Recette,
    "Facture": Facture,
}
