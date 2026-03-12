# services/ocr/pipeline/pipeline_ocr.py
#
# Ce module orchestre le pipeline OCR complet :
#  - conversion des fichiers uploadés en fichiers temporaires
#  - gestion du singleton PaddleOCRProcessor (pour éviter les réinitialisations GPU)
#  - appel du pipeline OCR défini dans ocr_processor.py
#
# Objectif : garder routes.py ultra-léger et isoler toute la logique métier ici.

import tempfile
# from services.ocr.ocr_processor import PaddleOCRProcessor
from services.service_instance import ocr_processor


# ---------------------------------------------------------------------------
# Singleton global du processor OCR
# ---------------------------------------------------------------------------
# PaddleOCRProcessor est très lourd à initialiser (modèles PaddleX, GPU, etc.).
# On ne doit l'instancier qu'une seule fois par process Flask.
# Sinon : crash, lenteur, ou device "undefined".
#
# ocr_processor = None signifie : "pas encore initialisé".
# ocr_processor = None


# def get_ocr_processor(use_llm=True, model="google/gemma-3-12b"):
#     """
#     Retourne l'instance unique (singleton) du PaddleOCRProcessor.
#     - Si elle n'existe pas encore → on la crée.
#     - Si elle existe → on met simplement à jour les paramètres dynamiques (ex: use_llm).
#     """
#     global ocr_processor

#     # Première initialisation : création du processor
#     if ocr_processor is None:
#         ocr_processor = PaddleOCRProcessor(
#             use_llm=use_llm,
#             use_model=model
#         )
#     else:
#         # Mise à jour dynamique du paramètre LLM
#         ocr_processor.use_llm = use_llm

#     return ocr_processor

# from services.ocr.ocr_processor import PaddleOCRProcessor
# Singleton OCR
# ocr_processor = PaddleOCRProcessor(
#     use_llm=True,
#     use_model="google/gemma-3-12b"
# )



# ---------------------------------------------------------------------------
# Conversion FileStorage → fichiers temporaires
# ---------------------------------------------------------------------------
# Flask fournit les fichiers uploadés sous forme d'objets FileStorage.
# PaddleOCR ne sait traiter que des chemins de fichiers (str).
# On convertit donc chaque upload en fichier temporaire sur le disque.
def save_uploaded_files(files):
    """
    Convertit une liste de FileStorage (upload Flask) en chemins de fichiers temporaires.
    Retourne une liste de chemins utilisables par PaddleOCR.
    """
    paths = []

    for file in files:
        # Création d'un fichier temporaire persistant (delete=False)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=file.filename)

        # Sauvegarde du contenu uploadé dans le fichier temporaire
        file.save(tmp.name)

        # On stocke le chemin pour le pipeline OCR
        paths.append(tmp.name)

    return paths


# ---------------------------------------------------------------------------
# Pipeline OCR complet
# ---------------------------------------------------------------------------
# Cette fonction est appelée depuis routes.py.
# Elle orchestre :
#   1. la conversion des fichiers uploadés
#   2. la récupération du processor (singleton)
#   3. l'exécution du pipeline OCR (défini dans ocr_processor.py)
def run_pipeline_ocr(files, use_llm=True):
    """
    Pipeline OCR complet :
    - Convertit les fichiers uploadés en fichiers temporaires
    - Récupère le processor OCR (singleton)
    - Exécute le pipeline OCR sur les images
    - Retourne les résultats prêts pour le template
    """
    # Étape 1 : conversion FileStorage → chemins temporaires
    paths = save_uploaded_files(files)

    # Étape 2 : récupération du processor (instanciation unique)
    ocr_processor.use_llm = use_llm

    # Étape 3 : exécution du pipeline OCR défini dans PaddleOCRProcessor
    return ocr_processor.run(paths)
