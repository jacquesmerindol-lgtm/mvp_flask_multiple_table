from functools import wraps

from services.schema import (
    RecetteSelection,
    ListeCourse,
    ListeRecetteSelection,
)
from services.service_instance import serviceListeCourse

from flask import request



# Imports LangChain

# ======================
# FONCTION PIPELINE
# ======================

# def pipeline(data: ListeRecetteSelection ) -> ListeCourse:
#     """
#     Orchestrateur principal pour le traitement des recettes.

#     Args:
#         data: Liste de recettes au format RecetteSelection

#     Returns:
#         serviceListeCourse._output_model: Résultat du traitement

#     Raises:
#         ValueError: Si les données d'entrée sont invalides
#         RuntimeError: En cas d'échec du traitement
#     """
#     # # Validation des données d'entrée
#     # if not isinstance(data, list):
#     #     raise ValueError("Input data must be a non-empty list of RecetteSelection")

#     # for recette in data:
#     #     if not isinstance(recette, RecetteSelection):
#     #         raise TypeError(f"All items must be RecetteSelection objects, got {type(recette)}")
#     #     if recette.nb_recette <= 0:
#     #         raise ValueError(f"nb_recette must be > 0 for {recette.nom_recette}")

#     # Instanciation et exécution du service
#     # serviceListeCourse = ListeCourses() déplacé dans service_instance
#     serviceListeCourse.set_input(data)

#     if serviceListeCourse._input_model is None:
#         raise ValueError("No input data provided")
#     else:
#         serviceListeCourse._output_model = serviceListeCourse.run()
#         if serviceListeCourse._output_model is None:
#             raise RuntimeError("Service returned no result")

#     # Stockage dans la session Flask si disponible
#     # try:
#     #     from flask import session
#     #     session["liste_course"] = serviceListeCourse._output_model.model_dump()
#     # except Exception:
#     #     pass

#     return serviceListeCourse._output_model
from flask import current_app
from services.service_instance import serviceListeCourse
from services.list_course.redis_store import (
    save_list_course_input,
    save_list_course_output,
)

def pipeline_liste_course(data: ListeRecetteSelection) -> ListeCourse:
    # # 🔥 Récupération du workflow_id global
    # workflow_id = current_app.config["WORKFLOW_ID"]

    # 1. Identifiant utilisateur stateless (cookie)
    user_id = request.cookies.get("user_id")

    # Stockage input
    save_list_course_input(user_id, data)

    # Appel du service stateless
    output = serviceListeCourse.run(data)

    # Stockage output
    save_list_course_output(user_id, output)

    return output
