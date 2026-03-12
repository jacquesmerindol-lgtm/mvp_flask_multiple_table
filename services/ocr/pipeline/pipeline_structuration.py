# services/ocr/pipeline/pipeline_structuration.py

# from services.ocr.structuration import StructurationLLM
# processor = StructurationLLM(
#     fieldname=item.get("image_path"),
#     schema_name=schema_name
# )
from services.service_instance import structuration_processor



def run_pipeline_structuration(results, schema_name="Recette"):
    """
    results : liste d'éléments OCR (dictionnaires ou objets)
    schema_name : nom du schéma Pydantic ("Recette", "Facture", etc.)
    """
    structuration_processor.schema_name = schema_name  
    return structuration_processor.run(results)
