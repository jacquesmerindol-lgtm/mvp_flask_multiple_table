#!/usr/bin/env python3
# ============================================================
#  StructurationLLM — Transformation d’un texte OCR en JSON structuré
# ============================================================
#
#  DESCRIPTION GÉNÉRALE
#  ---------------------
#  Cette classe applique un modèle LLM (hébergé via LM Studio ou tout
#  serveur OpenAI‑compatible) pour transformer un texte OCR brut en un
#  JSON strictement conforme à un schéma Pydantic prédéfini.
#
#  Contrairement à un OCR classique, cette classe n’extrait pas du texte :
#      → elle prend en entrée un texte déjà OCRisé (string)
#      → elle applique un modèle LLM pour structurer ce texte
#      → elle renvoie un JSON validé par un modèle Pydantic
#
#  Le schéma de sortie est sélectionné dynamiquement via un registre global :
#      SCHEMAS = { "Recette": Recette, "Facture": Facture, ... }
#
#  Le LLM reçoit :
#      - le texte OCR brut
#      - des instructions de formatage strictes générées automatiquement
#        par JsonOutputParser
#
#  Le résultat final est un JSON propre, validé, typé, prêt à être utilisé
#  dans un pipeline de traitement ou d’indexation.
#
#
#  OBJECTIF
#  --------
#  Garantir que le texte OCR brut soit converti en un JSON :
#      - propre
#      - complet
#      - strictement conforme au schéma Pydantic choisi
#      - sans hallucinations structurelles
#
#  Cette classe est idéale pour :
#      - structurer des recettes OCRisées
#      - structurer des factures OCRisées
#      - préparer des datasets JSON
#      - alimenter une base de données ou un moteur de recherche
#
#
#  PARAMÈTRES D’ENTRÉE
#  -------------------
#
#  - schema_name : str
#        Nom du schéma Pydantic à utiliser.
#        Exemple : "Recette", "Facture".
#
#  - model_name : str
#        Nom du modèle LLM utilisé pour la structuration.
#        Exemple : "openai/gpt-oss-20b".
#
#  - api_base : str
#        URL du serveur LM Studio ou OpenAI‑compatible.
#        Exemple : "http://localhost:1234/v1".
#
#  - temperature : float
#        Température du modèle (0.0 recommandé pour éviter les hallucinations).
#
#
#  SORTIES
#  -------
#  La méthode structure_text() retourne un dictionnaire Python conforme
#  au schéma Pydantic choisi :
#
#  Exemple :
#  {
#      "nom_recette": "...",
#      "ingredients": [...],
#      "etapes": [...],
#      ...
#  }
#
#  Le JSON est garanti valide :
#      → JsonOutputParser valide automatiquement la structure
#      → Pydantic valide les types et les champs obligatoires
#
#
#  DÉTAIL DU PIPELINE
#  -------------------
#  1. Sélection du schéma Pydantic via SCHEMAS[schema_name]
#
#  2. Génération automatique des instructions de formatage :
#       self.format_instructions = parser.get_format_instructions()
#
#     Ces instructions imposent au LLM :
#       - la structure exacte du JSON
#       - les champs obligatoires
#       - les types attendus
#
#  3. Construction du prompt :
#       - instructions de formatage
#       - texte OCR brut
#
#  4. Exécution de la chaîne LangChain :
#       texte → prompt → LLM → parser JSON → dict Python
#
#  5. Retour du JSON structuré
#
#
#  ROBUSTESSE & GESTION D’ERREURS
#  ------------------------------
#  - JsonOutputParser garantit que le LLM renvoie un JSON valide.
#  - Pydantic valide la structure finale.
#  - Le schéma peut être changé dynamiquement via set_schema().
#
#
#  LIMITES
#  -------
#  - La qualité dépend fortement du texte OCR en entrée.
#  - Le LLM peut halluciner du contenu si le texte OCR est trop pauvre.
#  - Le modèle doit être suffisamment performant pour suivre les
#    instructions de formatage strictes.
#
#
#  CAS D’USAGE TYPIQUES
#  ---------------------
#  - Structuration de recettes OCRisées
#  - Structuration de factures OCRisées
#  - Génération de datasets JSON
#  - Préparation de données pour RAG / embeddings
#
#
#  EXEMPLE D’UTILISATION
#  ----------------------
#  struct = StructurationLLM(schema_name="Recette")
#  json_data = struct.structure_text(texte_ocr)
#  print(json_data)
#
# ============================================================


from __future__ import annotations
from typing import Any, Dict, List, Type

from pydantic import BaseModel, Field, RootModel
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI


# =========================================================
# 1. Modèle Pydantic : schéma final 
# =========================================================

# # ----scémas input--- from ocr processor 
# class OCRResult(BaseModel):
#     image_path: str = ""
#     md_data: str = ""
#     enhanced_md: str = Field(default="", description="Markdown amélioré par LLM (optionnel)")

# class OCRResults(RootModel[List[OCRResult]]):
#     pass
from services.ocr.ocr_processor import OCRResults, OCRResult


# --- Tes schémas ---
class Ingredient(BaseModel):
    ingredient: str = Field(description="Nom de l’ingrédient, sans quantité.")
    quantite: str = Field(description="Quantité associée à l’ingrédient; répond non précisé si aucune quantité n'est mentionnée.")
    unite : str = Field(description="Unité associée à l’ingrédient; répond par une chaine de caractèrevide si aucune unité n'est mentionnée.")


class Recette(BaseModel):
    lien_fichier: str = Field(
        description="Chemin ou nom du fichier source."
    )

    nom_recette: str = Field(
        description="Nom exact de la recette tel qu'indiqué dans le texte."
    )

    nombre_personnes: int = Field(
        description="Nombre de personnes indiqué dans le texte."
    )

    duree_preparation: str = Field(
        description="Durée de préparation indiquée dans le texte."
    )

    duree_cuisson: str = Field(
        description="Durée de cuisson indiquée dans le texte."
    )

    duree_repos: str = Field(
        description="Durée de repos indiquée dans le texte, ou chaîne vide si absente."
    )

    liste_ingredients: List[Ingredient] = Field( 
        description=( 
            "Liste structurée de tous les ingrédients mentionnés dans la section ingrédients. "
            "Le champ 'ingredients' doit être une liste d'objets au format Ingredient: {nom, quantite}."
            "Chaque élément contient un nom d’ingrédient et une quantité séparée."
            "utilise uniquement les apostrophes typographiques ’ et non les apostrophes internes ' dans les phrases  ")
    )

    instructions: List[str] = Field(
        description="Étapes de préparation générales (section 'LA RECETTE'), en incluant les éléments listés dans la section PRÉPARATION AU ROBOT." )
    
    etapes_companion: List[str] = Field(
        description=(
            "Étapes spécifiques au robot Companion extraites du tableau : "
            "pour chaque ligne du tableau où la première colonne contient une étape, "
            "combiner le texte de la première colonne avec l'instruction de la colonne 'Companion'. "
            "Ignorer les lignes vides mais inclure les lignes d'accessoires. "
            "Si le tableau ne contient pas de colonne 'Companion', renvoyer ['néant']."
            "utilise uniquement les apostrophes typographiques ’ et non les apostrophes internes ' dans les phrases "
        )
    )

    astuce: str = Field(
        description="Conseils ou remarques éventuelles extraits du texte."
    )
    
class Facture(BaseModel):
    lien_fichier: str
    numero_facture: str
    fournisseur: str
    date: str
    montant_total: str
    lignes: List[str]

# Registre global des schémas disponibles
SCHEMAS: Dict[str, Type[BaseModel]] = {
    "Recette": Recette,
    "Facture": Facture,
}


# =========================================================
# 2. Classe principale de structuration
# =========================================================

class StructurationLLM:
    """
    Transforme un texte OCR en JSON structuré conforme au modèle Recette.
    """

    def __init__(
        self,
        fieldname:str = "",
        schema_name: str = "Recette",
        model_name: str = "mistralai/ministral-3-14b-instruct-2512",
        api_base: str = "http://100.121.195.119:1234/v1",
        temperature: float = 0.0,
        ):
        # ---------------------------------------------------------
        # Sélection dynamique du schéma Pydantic
        # ---------------------------------------------------------
        # schema_name est une chaîne ("Recette", "Facture", etc.)
        # SCHEMAS[schema_name] renvoie la classe Pydantic correspondante.
        self.schema_class = SCHEMAS[schema_name]

        # Parser JSON basé sur le schéma sélectionné
        self.parser = PydanticOutputParser(pydantic_object=self.schema_class)
        self.format_instructions = self.parser.get_format_instructions()
        self.fieldname = fieldname

        # Modèle textuel (LLM)
        self.llm = ChatOpenAI(
            model=model_name,
            openai_api_base=api_base,
            openai_api_key="not-needed",
            temperature=temperature,
        )

        # Propriétés internes - toujours initialisées
        self._input_model: OCRResults | None = None
        self._output_model: list[BaseModel] | None = None


        # Prompt de structuration
        template = """
Tu es un extracteur de données.

IMPORTANT :
Tu dois répondre STRICTEMENT avec un JSON valide.
Aucun texte avant ou après.
Aucun commentaire.
Aucun tag comme [THINK], [REASONING], etc.
Uniquement le JSON final.

Analyse le texte suivant et renvoie un objet au format pydantic strictement conforme aux instructions.

{format_instructions}

TEXTE :
{texte}

Fieldname du fichier texte :
{fieldname}
"""

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["texte"],
            partial_variables={"format_instructions": self.format_instructions, "fieldname": self.fieldname},
        )

        
    # def set_schema(self, schema_name: str):
    #     schema_class = SCHEMAS[schema_name]
    #     self.parser = JsonOutputParser(pydantic_object=schema_class)
    #     self.format_instructions = self.parser.get_format_instructions()

    # -----------------------------------------------------
    # Structurer un texte OCR brut
    # -----------------------------------------------------
    def structure_text(self, texte: str) -> Recette:
        """
        Transforme un texte OCR en objet pydantic structuré.
        """
        chain = (
            {
                "texte": RunnablePassthrough(),
                "fieldname": lambda _: self.fieldname,
                "format_instructions": lambda _: self.format_instructions,
            }
            | self.prompt
            | self.llm
            | self.parser
        )

        return chain.invoke({"texte": texte})
    
    def run(self, OCR_results: OCRResults) :
        self._input_model = OCR_results
        structured_items = [] 
        print("TYPE OCR:", type(OCR_results))

        for item in OCR_results.root:
            # 1) Récupération du texte OCR à structurer
            texte = item.enhanced_md or item.md_data

            if not texte:
                continue  # sécurité

            # 2) Récupération des fieldname du texte OCR à structurer
            self.fieldname = item.image_path

            # 3) Appel de la méthode correcte
            recette = self.structure_text(texte)
            structured_items.append(recette)
        
        # Construire le modèle Pydantic
        self._output_model = structured_items
        return self._output_model

# ---------------------------------------------------------
#  MAIN (DEBUG StructurationLLM)
# ---------------------------------------------------------
if __name__ == "__main__":
    import os
    import json

    print("\n=== DEBUG StructurationLLM ===\n")

    # Création du dossier output si nécessaire
    os.makedirs("output", exist_ok=True)

    # -----------------------------------------------------
    # Charger un texte OCR brut (exemple)
    # -----------------------------------------------------
    # Tu peux remplacer par un vrai fichier OCR
    ocr_text_path = "./image_enhanced.md"

    if os.path.exists(ocr_text_path):
        with open(ocr_text_path, "r", encoding="utf-8") as f:
            texte_ocr = f.read()
    else:
        texte_ocr = """
        Recette : Gâteau au chocolat
        Pour 6 personnes
        Ingrédients : chocolat, beurre, sucre, farine, œufs
        Étapes : mélanger, cuire 25 min
        """

    print("\n--- TEXTE OCR BRUT ---\n")
    print(texte_ocr)

    # -----------------------------------------------------
    # Configuration du LLM
    # -----------------------------------------------------
    schema_name = "Recette"   # ou "Facture"
    model_name = "mistralai/ministral-3-14b-instruct-2512"
    api_base = "http://localhost:1234/v1"
    temperature = 0.0

    struct = StructurationLLM(
        fieldname=ocr_text_path,
        schema_name=schema_name,
        model_name=model_name,
        api_base=api_base,
        temperature=temperature,
    )

    # -----------------------------------------------------
    # Structuration via LLM en Pydantic puis en JSON
    # -----------------------------------------------------
    print("\n--- STRUCTURATION EN COURS ---\n")
    pydantic_struct = struct.structure_text(texte_ocr)
    print(pydantic_struct)

    print("\n--- JSON STRUCTURÉ ---\n")
    print(json.dumps(pydantic_struct.model_dump_json(), indent=4, ensure_ascii=False))

    # -----------------------------------------------------
    # Sauvegarde du JSON structuré
    # -----------------------------------------------------
    output_path = f"output/structured_{schema_name.lower()}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pydantic_struct.model_dump(mode="json"), f, indent=4, ensure_ascii=False)

    print(f"\nJSON structuré sauvegardé dans : {output_path}")

    print("\n=== FIN DEBUG ===\n")
