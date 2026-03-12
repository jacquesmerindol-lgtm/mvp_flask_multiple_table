from functools import wraps

from services.list_course.schema import (
    RecetteSelection,
    ListeCourse
)
from services.service_instance import serviceListeCourse


# Imports LangChain

# ======================
# FONCTION PIPELINE
# ======================

def pipeline(data: list[RecetteSelection]) -> ListeCourse:
    """
    Orchestrateur principal pour le traitement des recettes.

    Args:
        data: Liste de recettes au format RecetteSelection

    Returns:
        serviceListeCourse._output_model: Résultat du traitement

    Raises:
        ValueError: Si les données d'entrée sont invalides
        RuntimeError: En cas d'échec du traitement
    """
    # Validation des données d'entrée
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Input data must be a non-empty list of RecetteSelection")

    for recette in data:
        if not isinstance(recette, RecetteSelection):
            raise TypeError(f"All items must be RecetteSelection objects, got {type(recette)}")
        if recette.nb_recette <= 0:
            raise ValueError(f"nb_recette must be > 0 for {recette.nom_recette}")

    # Instanciation et exécution du service
    # serviceListeCourse = ListeCourses() déplacé dans service_instance
    serviceListeCourse.set_input(data)

    serviceListeCourse._output_model = serviceListeCourse.run()
    if serviceListeCourse._output_model is None:
        raise RuntimeError("Service returned no result")

    # Stockage dans la session Flask si disponible
    try:
        from flask import session
        session["liste_course"] = serviceListeCourse._output_model.model_dump()
    except Exception:
        pass

    return serviceListeCourse._output_model