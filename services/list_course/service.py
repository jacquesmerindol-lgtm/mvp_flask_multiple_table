"""
Module Liste_courses.py - Génération de liste de courses à partir de recettes.
Architecture modulaire avec typage strict, gestion d'erreurs et CLI intégrée.
"""

from functools import wraps
import argparse
import json
import logging
from datetime import datetime
from typing import List

# Imports LangChain
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Imports Pydantic
from pydantic import BaseModel, Field
from services.list_course.schema import (
    RecetteSelection,
    ListeCourse,
    ListeRecetteSelection
)
#

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def safe(default_return=None):
    """Décorateur pour encapsuler une fonction dans un try/except avec logs complets."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in {func.__name__}")
                if default_return is not None:
                    return default_return
                raise
        return wrapper
    return decorator

# # ======================
# # MODÈLES PYDANTIC (dans schema.py)
# # ======================

# class Ingredient(BaseModel):
#     quantite: str =""
#     unite: str =""
#     ingredient: str

# class RecetteSelection(BaseModel):
#     id_recette: str
#     nb_recette: int
#     nom_livre: str
#     numero_livre: str =""
#     nom_recette: str
#     type_recette: str
#     liste_ingredients: list[Ingredient]

# class ListeCourse(BaseModel):
#     date_liste_course: datetime = Field(description="Date de la liste des courses")
#     liste_recette: list[RecetteSelection] = Field(description="Liste des recettes associées")
#     liste_course: str = Field(description="Liste des courses formatée")

# ======================
# CLASSE PRINCIPALE
# ======================

class ListeCourses:
    def __init__(
        self,
        model_name: str = "ministral-3-14b-instruct-2512",
        api_base: str = "http://localhost:1234/v1",
        temperature: float = 0.0
    ):
        """
        Initialise le service avec les paramètres du LLM.

        Args:
            model_name: Nom du modèle LLM
            api_base: URL de l'API LLM
            temperature: Température pour la génération (0.0 = déterministe)
        """
        self.model_name = model_name
        self.api_base = api_base
        self.temperature = temperature

        # Propriétés internes - toujours initialisées
        # self._input_model: ListeRecetteSelection | None = None
        # self._output_model: ListeCourse | None = None

        # Initialisation du modèle LLM
        self._model = ChatOpenAI(
            model=self.model_name,
            openai_api_base=self.api_base,
            openai_api_key="not-needed",
            temperature=self.temperature
        )

    # def set_input(self, data: ListeRecetteSelection) -> None:
    #     """
    #     Définit les données d'entrée pour le traitement.
    #     """
    #     # À ce stade, Pydantic a déjà validé `data`.
    #     # Aucune vérification supplémentaire n'est nécessaire.
    #     self._input_model = data

    # def run(self) -> ListeCourse | None:
    def run(self, data: ListeRecetteSelection) -> ListeCourse:
        """
        Exécute le traitement complet pour générer la liste de courses.

        Returns:
            ListeCourse: Résultat du traitement ou None en cas d'erreur
        """
        # if not self._input_model:
        #     logger.error("No input data provided")
        #     return None

        try:
            # Construction de la liste de courses via LLM
            # Correction : on passe la liste minimale au LLM
            # recettes_minimal: list[RecetteSelection]= self._input_model.recette_selection_items
            recettes_minimal: list[RecetteSelection] = data.recette_selection_items
            liste_courses = self._construire_liste_course(recettes_minimal)

            # Création du modèle de sortie
            output = ListeCourse(
                date_liste_course=datetime.now(),
                liste_recette=recettes_minimal,
                liste_course=liste_courses
            )

            # self._output_model = output
            return output

        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            return None

    @safe(default_return="")
    def _construire_liste_course(self, recettes: list[RecetteSelection]) -> str:
        """
        Méthode privée pour construire la liste de courses via LLM.

        Args:
            recettes: Liste des recettes à traiter

        Returns:
            str: Liste de courses formatée
        """
        prompt_template = '''
        Tu es un assistant qui doit réaliser une liste de courses de tous les ingrédients présents dans les recettes.
        Pour cela, tu devras :
            • Identifier les différentes recettes
            • considérer que des récettes qui apparaissent plusieurs fois sont des recettes différentes (ne pas mutualiser les ingrédients)
            • Pour chaque recette identifiée, identifier les ingrédients de chaque recette
            • Identifier chaque ingrédient identique et les regrouper.

        Ensuite tu devras présenter les ingrédients en respectant les catégories suivantes et l'ordre :
        {categorie}
        puis les sous catégories suivantes

        Pour ta réponse présente uniquement (et rien d'autre):
            • Les recettes listées
            • Les catégories et dans chaque catégorie les différents ingrédients en respectant l'ordre présenté précédemment. Pour chaque ingrédient, commencer par un point d'énumération, le nom de l'ingrédient, une tabulation, la parenthèse avec la quantité requise pour toutes les recettes en mentionnant le nom des recettes.

        Tu devras challenger ton résultat en relisant chaque recette, chaque ingrédient et vérifier que la quantité est bien présente entre paranthèse, qu'il n'y a pas de mutualisation entre recettes. Tu devras également relire ta réponse et vérifier que les ingrédients identiques ont bien été regroupés, qu'ils n'apparaissent pas plusieurs fois.

        Recettes : {recettes}
        '''

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["recettes"],
            partial_variables={"categorie": self._get_categories()}
        )

        chain = (
            {
                "recettes": RunnableLambda(self._preparer_recettes),
                "categorie": lambda _: self._get_categories(),
            }
            | prompt
            | self._model
            | StrOutputParser()
        )

        return chain.invoke(recettes)

    @safe(default_return="")
    def _preparer_recettes(self, recettes: list[RecetteSelection]) -> str:
        """
        Prétraite les recettes pour le LLM.

        Args:
            recettes: Liste des recettes

        Returns:
            str: Représentation textuelle des recettes
        """
        lignes = []
        for r in recettes:
            for _ in range(r.nb_recette):
                ingredients = ", ".join(
                    f"{ing.quantite} {ing.unite} {ing.ingredient}"
                    for ing in r.liste_ingredients
                )
                lignes.append(f"{r.nom_recette} : {ingredients}")
        return "\n".join(lignes)

    def _get_categories(self) -> list[str]:
        """Retourne la liste des catégories pour la classification."""
        return [
            "viandes", "saucisserie", "poissons_crustaces",
            "legumes", "fruits", "laitages", "herbes_condiments",
            "farines_pains_cereales", "sucres_levures",
            "bouillons_fonds", "boissons", "autres"
        ]

# # ======================
# # FONCTION PIPELINE
# # ======================

# def pipeline(data: list[RecetteSelection]) -> ListeCourse:
#     """
#     Orchestrateur principal pour le traitement des recettes.

#     Args:
#         data: Liste de recettes au format RecetteSelection

#     Returns:
#         ListeCourse: Résultat du traitement

#     Raises:
#         ValueError: Si les données d'entrée sont invalides
#         RuntimeError: En cas d'échec du traitement
#     """
#     # Validation des données d'entrée
#     if not isinstance(data, list) or len(data) == 0:
#         raise ValueError("Input data must be a non-empty list of RecetteSelection")

#     for recette in data:
#         if not isinstance(recette, RecetteSelection):
#             raise TypeError(f"All items must be RecetteSelection objects, got {type(recette)}")
#         if recette.nb_recette <= 0:
#             raise ValueError(f"nb_recette must be > 0 for {recette.nom_recette}")

#     # Instanciation et exécution du service
#     service = ListeCourses()
#     service.set_input(data)

#     result = service.run()
#     if result is None:
#         raise RuntimeError("Service returned no result")

#     # Stockage dans la session Flask si disponible
#     try:
#         from flask import session
#         session["liste_course"] = result.model_dump()
#     except Exception:
#         pass

#     return result

# ======================
# CLI INTEGRÉE
# ======================

# def main():
#     """Interface en ligne de commande pour tester le service."""
#     parser = argparse.ArgumentParser(description="Générateur de liste de courses à partir de recettes")
#     parser.add_argument("--input-file", type=str, help="Fichier JSON contenant les recettes d'entrée")

#     args = parser.parse_args()

#     # Chargement des données
#     if args.input_file:
#         try:
#             with open(args.input_file) as f:
#                 data = json.load(f)
#             recettes = [RecetteSelection(**item) for item in data]
#         except Exception as e:
#             logger.error(f"Failed to load input file: {str(e)}")
#             return
#     else:
#         # Données par défaut du notebook
#         recettes = [
#             RecetteSelection(
#                 id_recette="1",
#                 nb_recette=1,
#                 nom_livre="Cuisine Traditionnelle",
#                 numero_livre="2",
#                 nom_recette="Poulet au vin rouge",
#                 type_recette="plat principal",
#                 liste_ingredients=[
#                     {"ingredient": "poulet", "quantite": "1"},
#                     {"ingredient": "vin rouge", "quantite": "1 bouteille"},
#                     {"ingredient": "oignons", "quantite": "3"},
#                     {"ingredient": "ail", "quantite": "4 gousses"},
#                 ]
#             ),
#             RecetteSelection(
#                 id_recette="2",
#                 nb_recette=2,
#                 nom_livre="Cuisine Traditionnelle",
#                 numero_livre="2",
#                 nom_recette="Salade César",
#                 type_recette="entrée",
#                 liste_ingredients=[
#                     {"ingredient": "laitue", "quantite": "1"},
#                     {"ingredient": "tomate", "quantite": "2"},
#                     {"ingredient": "oignons", "quantite": "200 grammes"},
#                     {"ingredient": "ail", "quantite": "2 gousses"},
#                 ]
#             )
#         ]

#     # Exécution du pipeline
#     try:
#         result = pipeline(recettes)
#         print("\n=== Résultat de la liste de courses ===")
#         print(result.liste_course)

#         output_json = {
#             "date": result.date_liste_course.isoformat(),
#             "recettes": [r.model_dump() for r in result.liste_recette],
#             "liste_course": result.liste_course.split("\n")
#         }
#         print("\n=== Structure JSON ===")
#         print(json.dumps(output_json, indent=2, default=str))

#     except Exception as e:
#         logger.error(f"Pipeline execution failed: {str(e)}")

# if __name__ == "__main__":
#     main()
