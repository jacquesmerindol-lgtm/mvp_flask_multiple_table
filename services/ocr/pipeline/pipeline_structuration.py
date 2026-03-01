# services/ocr/pipeline/pipeline_structuration.py

from services.ocr.structuration import StructurationLLM

def run_pipeline_structuration(results, schema_name="Recette"):
    """
    results : liste d'éléments OCR (dictionnaires ou objets)
    schema_name : nom du schéma Pydantic ("Recette", "Facture", etc.)
    """

    structured_results = []

    for item in results:

        # 1) Récupération du texte OCR à structurer
        texte = item.get("enhanced_md") or item.get("md_data")

        if not texte:
            continue  # sécurité

        # 2) Instanciation du processor pour ce schéma
        processor = StructurationLLM(
            fieldname=item.get("image_path"),
            schema_name=schema_name
        )

        # 3) Appel de la méthode correcte
        structured = processor.structure_text(texte)

        # 4) Ajout du résultat Pydantic dans la liste
        structured_results.append(structured)

    return structured_results
