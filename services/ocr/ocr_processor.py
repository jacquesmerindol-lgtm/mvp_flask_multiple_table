# ============================================================
#  PaddleOCRProcessor — Pipeline OCR complet basé sur PaddleOCR V3
# ============================================================
#
#  DESCRIPTION GÉNÉRALE
#  ---------------------
#  Cette classe encapsule un pipeline OCR complet utilisant
#  PP-StructureV3 (PaddleOCR) pour extraire du texte structuré
#  depuis :
#      - des images (JPG, PNG…)
#      - des documents PDF (multi‑pages inclus)
#
#  PP‑StructureV3 gère nativement les PDF : chaque page est
#  traitée comme une image interne par PaddleOCR.
#
#  Le pipeline réalise automatiquement :
#    1. Détection et reconnaissance OCR (PP‑StructureV3)
#    2. Extraction du markdown généré par PaddleOCR
#    3. Conversion des blocs HTML → Markdown (tableaux, div, img…)
#    4. Suppression des images Markdown (![](...))
#    5. Concaténation multi‑pages sécurisée
#    6. (Optionnel) Amélioration du markdown via un LLM local
#    7. Sauvegarde du markdown final
#
#
#  OBJECTIF
#  --------
#  Produire un document Markdown propre, lisible, structuré,
#  sans images, et prêt à être utilisé dans un pipeline de
#  traitement de recettes, documents ou extraction de données.
#
#
#  PARAMÈTRES D’ENTRÉE
#  -------------------
#
#  - image_paths : List[str]
#        Liste des chemins d’images ou PDF à traiter.
#
#  - lang : str
#        Langue du modèle OCR (ex: "fr", "en", "ch").
#
#  - use_doc_orientation_classify : bool
#        Active la détection d’orientation du document.
#
#  - use_doc_unwarping : bool
#        Active la correction de perspective.
#
#  - use_textline_orientation : bool
#        Active la correction d’orientation des lignes de texte.
#
#  - use_llm : bool
#        Si True → amélioration du markdown via un LLM local
#        (serveur compatible OpenAI, ex : LM Studio).
#
#  - use_model : str
#        Nom du modèle LLM utilisé pour l’amélioration du markdown.
#        Exemple : "google/gemma-3-12b".
#
#  - use_base_url : str
#        URL du serveur compatible OpenAI.
#        Exemple : "http://127.0.0.1:1234/v1".
#
#  - use_api_key : str
#        Clé API utilisée pour communiquer avec le serveur LLM.
#        Exemple : "lm-studio".
#
#  - use_temperature : float
#        Température du modèle LLM (0.0 = déterministe, 1.0 = créatif).
#
#
#  SORTIES
#  -------
#  La méthode run_pipeline() retourne une liste de dictionnaires :
#
#  [
#      {
#          "image_path": "chemin/vers/image_ou_pdf",
#          "md_data": "<markdown propre sans images>",
#          "enhanced_md": "<markdown amélioré par LLM>"  # si use_llm=True
#      },
#      ...
#  ]
#
#
#  DÉTAIL DU PIPELINE
#  -------------------
#  1. PP-StructureV3 prédit la structure du document :
#       - titres
#       - paragraphes
#       - tableaux
#       - images
#       - zones de texte
#
#     ⚠️ Pour les PDF :
#        PP‑StructureV3 traite automatiquement chaque page.
#
#  2. Le markdown brut généré par PaddleOCR contient :
#       - du markdown natif
#       - des blocs HTML (table, div, img)
#
#  3. convert_html_blocks_to_markdown()
#       Convertit uniquement les blocs HTML → Markdown
#       sans toucher au reste du texte.
#
#  4. remove_markdown_images()
#       Supprime toutes les images Markdown (![](...))
#       pour obtenir un document 100% texte.
#
#  5. safe_concatenate_markdown()
#       Concatène plusieurs pages en un seul markdown.
#       Utilise la fonction Paddle si possible, sinon fallback.
#
#  6. enhance_with_llm()
#       - Si l’entrée est une image → 1 appel LLM
#       - Si l’entrée est un PDF → conversion PDF → images
#         puis 1 appel LLM par page
#       Le LLM corrige la structure, l’orthographe, etc.
#       (sans jamais modifier la structure des tableaux).
#
#  7. save_markdown()
#       Sauvegarde le markdown final dans un fichier .md.
#
#
#  ROBUSTESSE & GESTION D’ERREURS
#  ------------------------------
#  - Le décorateur @safe encapsule automatiquement les fonctions
#    dans un try/except centralisé.
#
#  - En cas d’erreur :
#       → log propre
#       → fallback intelligent
#       → le pipeline continue sans planter
#
#  - Les PDF convertis en images via pdf2image sont traités
#    en mémoire (aucun fichier temporaire conservé).
#
# ============================================================
#
#
#  CAS D’USAGE TYPIQUES
#  ---------------------
#  - OCR de recettes de cuisine
#  - OCR de documents scannés
#  - Extraction de tableaux
#  - Nettoyage de documents OCR pour LLM
#  - Préparation de datasets Markdown
#
#
#  EXEMPLE D’UTILISATION
#  ----------------------
#  processor = PaddleOCRProcessor(use_llm=True, use_model="google/gemma-3-12b")
#  results = processor.run_pipeline(["./image1.jpg", "./image2.png"])
#
#  for item in results:
#      print(item["md_data"])
#      print(item.get("enhanced_md", ""))
#
# ============================================================
#  DÉPENDANCES REQUISES
# ============================================================
#
#  OCR & STRUCTURATION
#  -------------------
#  paddleocr
#  paddlex[ocr]        (⚠️ à installer en dernier, après langchain)
#
#  DOCUMENTS
#  ---------
#  python-docx
#  markdownify
#
#  PDF → IMAGES
#  ------------
#  pdf2image          (conversion PDF → images pour le LLM)
#  Poppler            (dépendance système requise par pdf2image)
#
#  LLM & LANGCHAIN
#  ---------------
#  langchain<1.0.0    (compatibilité avec paddlex[ocr])
#  langchain-core
#  langchain-openai
#  langsmith
#
#
# ============================================================
#  INSTALLATION DES DÉPENDANCES
# ============================================================
#
#  1) Mettre à jour pip
#  ---------------------
#  python -m pip install --upgrade pip
#
#
#  2) Installation de PaddlePaddle
#  -------------------------------
#  Documentation officielle :
#      https://www.paddlepaddle.org.cn/documentation/docs/en/install/index_en.html
#
#  Vérifier la version CUDA installée :
#      nvidia-smi
#
#  GPU — version pour CUDA 12.9 + cuDNN 9.9 :
#      python -m pip install paddlepaddle-gpu==3.3.0 \
#          -i https://www.paddlepaddle.org.cn/packages/stable/cu129/
#
#  CPU — version stable (la 3.3.0 CPU ne fonctionne pas) :
#      python -m pip install paddlepaddle==3.2.2 \
#          -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
#
#
#  3) Installation PaddleOCR + PaddleX
#  -----------------------------------
#      python -m pip install paddleocr
#      python -m pip install "paddlex[ocr]"
#
#
#  4) Installation des librairies LLM
#  ----------------------------------
#      python -m pip install "langchain<1.0.0"
#      python -m pip install langchain-core
#      python -m pip install langchain-openai
#      python -m pip install langsmith
#
#
#  5) Installation des outils Markdown / Word
#  ------------------------------------------
#      python -m pip install python-docx
#      python -m pip install markdownify
#
#
#  6) Installation de pdf2image + Poppler
#  --------------------------------------
#  # Librairie Python
#      python -m pip install pdf2image
#
#  # Dépendance système Poppler :
#  # Windows : télécharger Poppler ici :
#      https://github.com/oschwartz10612/poppler-windows/releases/
#
#  # Puis ajouter le dossier "poppler-xx/bin" au PATH système.
#
# ============================================================
#

from paddleocr import PPStructureV3
import subprocess
from typing import List, TypedDict
import base64
import re
import traceback
from io import BytesIO
import os

from markdownify import markdownify as md
from langchain_openai import ChatOpenAI
from pdf2image import convert_from_path


# Typings
ImageFilePaths = List[str]


class OCRResult(TypedDict):
    image_path: str
    md_data: str
    enhanced_md: str  # Markdown amélioré par LLM (optionnel)


OCRResults = List[OCRResult]


# ---------------------------------------------------------
#  Décorateur SAFE
# ---------------------------------------------------------
def safe(default_return=None):
    """
    Décorateur pour encapsuler automatiquement une fonction dans un try/except.
    - Log l’erreur proprement
    - Retourne une valeur par défaut configurable
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.log_error(f"Erreur dans {func.__name__}()", e)
                return default_return
        return wrapper
    return decorator


class PaddleOCRProcessor:
    """
    Pipeline complet :
    - PP-StructureV3
    - Conversion HTML → Markdown
    - Suppression des images
    - Amélioration LLM (optionnel)
    - Gestion d’erreurs centralisée via @safe
    """

    def __init__(
        self,
        lang: str = "fr",
        use_doc_orientation_classify: bool = True,
        use_doc_unwarping: bool = True,
        use_textline_orientation: bool = True,
        use_llm: bool = False,
        use_model: str = "google/gemma-3-12b",
        use_base_url: str = "http://100.121.195.119:1234/v1",
        use_api_key: str = "lm-studio",
        use_temperature: float = 0.0,
    ):
        self.lang = lang
        self.use_doc_orientation_classify = use_doc_orientation_classify
        self.use_doc_unwarping = use_doc_unwarping
        self.use_textline_orientation = use_textline_orientation
        self.use_llm = use_llm

        # Paramètres LLM
        self.use_model = use_model
        self.use_base_url = use_base_url
        self.use_api_key = use_api_key
        self.use_temperature = use_temperature

        self.pipeline = self._init_pipeline()

    # ---------------------------------------------------------
    #  Logger centralisé
    # ---------------------------------------------------------
    def log_error(self, message: str, exception: Exception):
        print("\n[❌ ERREUR] " + message)
        print("   →", str(exception))
        traceback.print_exc()

    # ---------------------------------------------------------
    #  GPU detection
    # ---------------------------------------------------------
    @staticmethod
    def has_nvidia_gpu() -> bool:
        try:
            subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False

    # ---------------------------------------------------------
    #  HTML → Markdown
    # ---------------------------------------------------------
    @safe(default_return="")
    def convert_html_blocks_to_markdown(self, markdown_text: str) -> str:
        pattern = r"<(?:table|div|html|body)[\s\S]*?</(?:table|div|html|body)>"
        html_blocks = re.findall(pattern, markdown_text, flags=re.IGNORECASE)
        img_blocks = re.findall(r"<img[^>]+?>", markdown_text, flags=re.IGNORECASE)

        for block in html_blocks + img_blocks:
            md_block = md(block, heading_style="ATX")
            markdown_text = markdown_text.replace(block, md_block)

        return markdown_text

    # ---------------------------------------------------------
    #  Suppression des images Markdown
    # ---------------------------------------------------------
    @safe(default_return="")
    def remove_markdown_images(self, markdown_text: str) -> str:
        return re.sub(r"!\[[^\]]*\]\([^)]+\)", "", markdown_text)

    # ---------------------------------------------------------
    #  Concaténation multi-pages sécurisée
    # ---------------------------------------------------------
    @safe(default_return="")
    def safe_concatenate_markdown(self, markdown_list: List[str]) -> str:
        if len(markdown_list) == 1:
            return markdown_list[0]

        try:
            return self.pipeline.concatenate_markdown_pages(markdown_list)
        except Exception:
            print("[⚠] Fallback : concaténation simple")
            return "\n\n".join(markdown_list)

    # ---------------------------------------------------------
    #  Pipeline initialization
    # ---------------------------------------------------------
    @safe(default_return=None)
    def _init_pipeline(self) -> PPStructureV3:
        if self.has_nvidia_gpu():
            return PPStructureV3(
                lang=self.lang,
                use_doc_orientation_classify=self.use_doc_orientation_classify,
                use_doc_unwarping=self.use_doc_unwarping,
                use_textline_orientation=self.use_textline_orientation,
                device="gpu",
            )
        else:
            return PPStructureV3(
                lang=self.lang,
                use_doc_orientation_classify=self.use_doc_orientation_classify,
                use_doc_unwarping=self.use_doc_unwarping,
                use_textline_orientation=self.use_textline_orientation,
            )

    # ---------------------------------------------------------
    #  Utilitaire : image PIL → base64
    # ---------------------------------------------------------
    @safe(default_return="")
    def pil_image_to_base64(self, image) -> str:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode("utf-8")

    # ---------------------------------------------------------
    #  Utilitaire : chemin image → base64
    # ---------------------------------------------------------
    @safe(default_return="")
    def image_path_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return base64.b64encode(image_bytes).decode("utf-8")

    # ---------------------------------------------------------
    #  Run OCR pipeline
    # ---------------------------------------------------------
    @safe(default_return=[])
    def run_pipeline(self, image_paths: ImageFilePaths) -> OCRResults:
        results: OCRResults = []

        for image_path in image_paths:
            # PP-StructureV3 accepte directement les PDF et les images
            try:
                raw = self.pipeline.predict(image_path)
            except Exception as e:
                self.log_error(f"Erreur PaddleOCR sur l’entrée : {image_path}", e)
                results.append(
                    {"image_path": image_path, "md_data": "", "enhanced_md": ""}
                )
                continue

            markdown_list = []

            for res in raw:
                md_raw = res.markdown.get("markdown_texts", "")
                md_clean = self.convert_html_blocks_to_markdown(md_raw)
                md_clean = self.remove_markdown_images(md_clean)
                markdown_list.append(md_clean)

            markdown_texts = self.safe_concatenate_markdown(markdown_list)

            result_item = {
                "image_path": image_path,
                "md_data": markdown_texts,
            }

            if self.use_llm:
                enhanced = self.enhance_with_llm(image_path, markdown_texts)
                result_item["enhanced_md"] = enhanced

            results.append(result_item)

        return results

    # ---------------------------------------------------------
    #  LLM Enhancement (gère images et PDF)
    # ---------------------------------------------------------
    @safe(default_return="")
    def enhance_with_llm(self, input_path: str, markdown_texts: str) -> str:
        """
        Si input_path est une image → 1 appel LLM.
        Si input_path est un PDF → pdf2image, 1 page = 1 appel LLM,
        puis concaténation des résultats.
        """
        llm = ChatOpenAI(
            model=self.use_model,
            base_url=self.use_base_url,
            api_key=self.use_api_key,
            temperature=self.use_temperature,
        )

        system_msg = {
            "role": "system",
            "content": (
                "Tu es un assistant expert en structuration de documents OCR.\n"
                "Tu dois renvoyer un document markdown propre, structuré, cohérent.\n\n"
                "⚠️ RÈGLE ABSOLUE SUR LES TABLEAUX :\n"
                "- Ne jamais modifier la structure.\n"
                "- Ne jamais changer le nombre de lignes/colonnes.\n"
                "- Ne jamais réorganiser.\n"
                "- Correction interne des cellules uniquement.\n"
                "- Aucun commentaire."
            ),
        }

        enhanced_chunks: List[str] = []

        # Cas PDF : conversion en images, 1 page = 1 appel LLM
        if input_path.lower().endswith(".pdf"):
            pages = convert_from_path(input_path)
            for page_index, page in enumerate(pages, start=1):
                image_b64 = self.pil_image_to_base64(page)

                user_msg = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Page {page_index} du PDF.\n"
                                "Voici le markdown OCR brut correspondant :\n"
                                f"{markdown_texts}\n\n"
                                "Renvoie un markdown corrigé et structuré."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            },
                        },
                    ],
                }

                response = llm.invoke([system_msg, user_msg])
                enhanced_chunks.append(response.content)

            return "\n\n".join(enhanced_chunks)

        # Cas image simple
        else:
            image_b64 = self.image_path_to_base64(input_path)

            user_msg = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Voici l'image du document.\n"
                            "Voici le markdown OCR brut :\n"
                            f"{markdown_texts}\n\n"
                            "Renvoie un markdown corrigé et structuré."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }

            response = llm.invoke([system_msg, user_msg])
            return response.content

    # ---------------------------------------------------------
    #  Save Markdown
    # ---------------------------------------------------------
    @safe(default_return=None)
    def save_markdown(self, md_content: str, output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)


# ---------------------------------------------------------
#  MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    processor = PaddleOCRProcessor(use_llm=True, use_model="google/gemma-3-12b")

    list_image_path: ImageFilePaths = ["./image.pdf", "./image1.png"]
    results = processor.run_pipeline(list_image_path)

    for item in results:
        image_path = item["image_path"]
        base = os.path.splitext(os.path.basename(image_path))[0]

        # Markdown brut PP-Structure
        md_output_path = f"output/{base}.md"
        processor.save_markdown(item["md_data"], md_output_path)
        print(f"Markdown sauvegardé dans : {md_output_path}")

        # Markdown amélioré LLM
        if processor.use_llm:
            md_output_path = f"output/{base}_enhanced.md"
            processor.save_markdown(item["enhanced_md"], md_output_path)
            print(f"Markdown amélioré sauvegardé dans : {md_output_path}")
