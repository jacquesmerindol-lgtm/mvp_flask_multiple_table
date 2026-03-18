# # services/ocr/pipeline/pipeline_structuration.py

# # from services.ocr.structuration import StructurationLLM
# # processor = StructurationLLM(
# #     fieldname=item.get("image_path"),
# #     schema_name=schema_name
# # )
# from services.service_instance import structuration_processor



# def run_pipeline_structuration(results, schema_name="Recette"):
#     """
#     results : liste d'éléments OCR (dictionnaires ou objets)
#     schema_name : nom du schéma Pydantic ("Recette", "Facture", etc.)
#     """
#     structuration_processor.schema_name = schema_name  
#     return structuration_processor.run(results)

# services/structuration/pipeline_structuration.py

import json
from flask import request
from app.redis_client import redis_client
from services.service_instance import structuration_processor
from services.schema import OCRResults


def run_pipeline_structuration(ocr_results: OCRResults, schema_name="Recette"):
    """
    Pipeline stateless de structuration :
    - lit user_id depuis le cookie
    - stocke l'OCR brut dans Redis (input)
    - exécute StructurationLLM
    - stocke le JSON structuré dans Redis (output)
    - renvoie la liste de modèles Pydantic
    """

    # 1. Identifiant utilisateur stateless
    user_id = request.cookies.get("user_id")

    # 2. Stockage input OCR
    redis_client.set(
        f"structuration:{user_id}:input",
        ocr_results.model_dump_json()
    )

    # 3. Configuration dynamique du schéma
    structuration_processor.schema_name = schema_name

    # 4. Exécution du service stateless
    structured_items = structuration_processor.run(ocr_results)

    # 5. Conversion en JSON pour Redis
    payload = [item.model_dump(mode="json") for item in structured_items]

    redis_client.set(
        f"structuration:{user_id}:output",
        json.dumps(payload, ensure_ascii=False)
    )

    return structured_items
