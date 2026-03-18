from flask import Blueprint, render_template, request, session, redirect, url_for, flash,  Response, current_app
from database import get_db
from services.list_course.pipeline import pipeline_liste_course
from typing import Any
from crud import course_crud   

from services.list_course.logic import build_selection_pydantic

from services.list_course.crud import (
    get_recettes_filtered,
    get_recettes_by_ids,
)

from services.list_course.logic import build_recette_map

from services.service_instance import serviceListeCourse
from services.schema import RecetteSelection, ListeRecetteSelection, RecetteQuantifiee, ListeRecetteQuantifiee, ListeCourse

from app.redis_client import redis_client

# ----------------------------------------------------------------------
# Sélection : ajout de recettes à la sélection (avec addition des quantités)
# ----------------------------------------------------------------------
ingredients_bp = Blueprint("recettes_ui", __name__, url_prefix="/ingredients")

def load_selection_from_redis() -> ListeRecetteSelection:
    # workflow_id = current_app.config["WORKFLOW_ID"]
    user_id = request.cookies.get("user_id")
    raw = redis_client.get(f"courses:{user_id}:selection")
    if not raw:
        return ListeRecetteSelection(recette_selection_items=[])
    return ListeRecetteSelection.model_validate_json(raw)


def save_selection_to_redis(selection: ListeRecetteSelection) -> None:
    # workflow_id = current_app.config["WORKFLOW_ID"]
    user_id = request.cookies.get("user_id")
    redis_client.set(
        f"courses:{user_id}:selection",
        selection.model_dump_json()
    )

@ingredients_bp.route("/select", methods=["GET", "POST"])
def select_ui() -> Response:
    """
    Gère la sélection de recettes :
    - POST : ajoute des recettes à la sélection (avec addition des quantités)
    - GET  : affiche les recettes filtrées + la sélection existante
    """

    # ----------------------------------------------------------------------
    # POST : ajout de recettes à la sélection
    # ----------------------------------------------------------------------
    if request.method == "POST":

        # Liste des IDs cochés dans le formulaire
        selected_ids: list[str] = request.form.getlist("selected_recettes")

        # Si rien n'est sélectionné → retour à la page
        if not selected_ids:
            return redirect(url_for("recettes_ui.select_ui"))

        # ------------------------------------------------------------------
        # 1) Récupérer le modèle enrichi existant (ou une liste vide)
        # ------------------------------------------------------------------
        # enriched: ListeRecetteSelection = (
        #     serviceListeCourse._input_model
        #     or ListeRecetteSelection(recette_selection_items=[])
        # )
        enriched = load_selection_from_redis()

        # ------------------------------------------------------------------
        # 2) Reconstruire un modèle minimal à partir du modèle enrichi
        #    (id_recette + nb_recette uniquement)
        # ------------------------------------------------------------------
        minimal = ListeRecetteQuantifiee(
            items=[
                RecetteQuantifiee(
                    id_recette=item.id_recette,
                    nb_recette=item.nb_recette
                )
                for item in enriched.recette_selection_items
            ]
        )

        # ------------------------------------------------------------------
        # 3) Convertir en dict temporaire pour additionner les quantités
        # ------------------------------------------------------------------
        nb_map: dict[str, int] = {
            item.id_recette: item.nb_recette
            for item in minimal.items
        }

        # Ajout / addition des quantités envoyées par le formulaire
        for rid in selected_ids:
            nb_new: int = int(request.form.get(f"nb_recette_{rid}", 1))
            nb_map[rid] = nb_map.get(rid, 0) + nb_new

        # ------------------------------------------------------------------
        # 4) Reconstruire un modèle minimal propre
        # ------------------------------------------------------------------
        minimal = ListeRecetteQuantifiee(
            items=[
                RecetteQuantifiee(id_recette=k, nb_recette=v)
                for k, v in nb_map.items()
            ]
        )

        # ------------------------------------------------------------------
        # 5) Construire le modèle enrichi final
        # ------------------------------------------------------------------
        enriched = build_selection_pydantic(minimal)

        # ------------------------------------------------------------------
        # 6) Stocker uniquement le modèle enrichi (pas le minimal)
        # ------------------------------------------------------------------
        # serviceListeCourse._input_model = enriched
        save_selection_to_redis(enriched)

        # ------------------------------------------------------------------
        # 7) Recharger les recettes SQLAlchemy pour affichage
        # ------------------------------------------------------------------
        ids: list[str] = [item.id_recette for item in enriched.recette_selection_items]
        recettes = get_recettes_by_ids(ids)
        recette_map = build_recette_map(recettes)

        return render_template(
            "select_recettes/selection_result.html",
            selected_data=enriched.recette_selection_items,
            recette_map=recette_map,
        )

    # ----------------------------------------------------------------------
    # GET : affichage + filtres
    # ----------------------------------------------------------------------
    # enriched: ListeRecetteSelection | None = serviceListeCourse._input_model
    enriched = load_selection_from_redis()

    # Lecture des filtres
    f_periode: str | None = request.args.get("periode")
    f_robot: str | None = request.args.get("robot")
    f_nom: str | None = request.args.get("nom")
    f_type: str | None = request.args.get("type")

    # Récupération des recettes filtrées
    rows = get_recettes_filtered(
        periode=f_periode,
        robot=f_robot,
        nom_recette=f_nom,
        type_recette=f_type,
    )

    # Construction des valeurs de filtres disponibles
    all_periodes = sorted({p for r in rows for p in r.periode_recettes})
    all_robots = sorted({r.nom_robot for r in rows})
    all_types = sorted({r.type_recette for r in rows})

    # Mapping SQLAlchemy pour les recettes sélectionnées
    recette_map: dict[str, Any] = {}
    if enriched:
        ids = [item.id_recette for item in enriched.recette_selection_items]
        recettes = get_recettes_by_ids(ids)
        recette_map = build_recette_map(recettes)

    return render_template(
        "select_recettes/select.html",
        rows=rows,
        all_periodes=all_periodes,
        all_robots=all_robots,
        all_types=all_types,
        f_periode=f_periode,
        f_robot=f_robot,
        f_nom=f_nom,
        f_type=f_type,
        selected_data=enriched.recette_selection_items if enriched else [],
        recette_map=recette_map,
    )
    # Tu passes au template :
    #     rows : les recettes filtrées à afficher
    #     all_periodes / all_robots / all_types : les valeurs pour les filtres
    #     f_periode / f_robot / f_nom / f_type : les filtres actifs (pour pré-remplir l’UI)
    #     selected_data : la sélection actuelle (liste de RecetteSelection)
    #     recette_map : les objets SQLAlchemy complets pour les recettes sélectionnées

# ----------------------------------------------------------------------
# PAGE DE MISE À JOUR DE LA SÉLECTION
# ----------------------------------------------------------------------

@ingredients_bp.route("/select/update", methods=["GET", "POST"])
def update_selection():

    # selected_data_pydantic: ListeRecetteSelection = (
    #     serviceListeCourse._input_model
    #     or ListeRecetteSelection(recette_selection_items=[])
    # )
    selected_data_pydantic: ListeRecetteSelection = load_selection_from_redis()


    # ----------------------------------------------------------------------
    # POST : suppression ou modification
    # ----------------------------------------------------------------------
    if request.method == "POST":
            
        # --- SUPPRESSION D’UNE RECETTE DE LA SÉLECTION ---

        # On récupère la valeur du bouton "delete" si l’utilisateur a cliqué dessus.
        # Le bouton a name="delete" et value="{{ item.id_recette }}"
        rid_to_delete = request.form.get("delete")

        if rid_to_delete:
            # Si un id est présent, on filtre la liste pour retirer l’élément correspondant.
            # selected_data_pydantic est une liste de RecetteSelection.
            selected_data_pydantic = ListeRecetteSelection(
                recette_selection_items=[
                    item for item in selected_data_pydantic.recette_selection_items
                    if item.id_recette != rid_to_delete
                ]
            )

            # On met à jour le modèle interne du service.
            # serviceListeCourse._input_model = selected_data_pydantic
            save_selection_to_redis(selected_data_pydantic)

            # On recharge la page pour afficher la liste mise à jour.
            return redirect(url_for("recettes_ui.update_selection"))


        # --- MISE À JOUR DES QUANTITÉS POUR CHAQUE RECETTE ---
        # créer un nouvel objet pydantic qui sera mis à jour pour conserver l'immuabilité
        updated_list = []

        # On parcourt chaque recette sélectionnée.
        for item in selected_data_pydantic.recette_selection_items:

            # On récupère la nouvelle quantité envoyée par le formulaire.
            # Le champ a name="nb_recette_<id>"
            new_value = request.form.get(f"nb_recette_{item.id_recette}")
            
            if new_value:
                # On met à jour le nouvel objet Pydantic.
                updated_item = item.model_copy(update={"nb_recette": int(new_value)})
            else:
                # on conserve la valeur précédente pour le nouvel objet pydantic
                updated_item = item

            # On ajoute l’objet (modifié ou non) à la liste mise à jour.
            updated_list.append(updated_item)
        # on recrée un nouvel objet pydantic ListeRecetteSelection à partir de la liste mise à jour
        updated_list_pydantic = ListeRecetteSelection(recette_selection_items=updated_list)

        # On sauvegarde la nouvelle liste dans le service.
        # serviceListeCourse._input_model = updated_list_pydantic
        save_selection_to_redis(updated_list_pydantic)

        # On recharge la page pour afficher les nouvelles quantités.
        return redirect(url_for("recettes_ui.update_selection"))


    # --- GET : affichage de la sélection actuelle ---

    # On extrait uniquement les identifiants des recettes sélectionnées.
    # selected_data_pydantic est une liste de RecetteSelection (modèles Pydantic).
    ids = [item.id_recette for item in selected_data_pydantic.recette_selection_items]

    # On recharge depuis la base les objets Recette SQLAlchemy correspondant à ces IDs.
    # Cela permet d’obtenir toutes les informations métier (nom, type, robot, etc.).
    recettes = get_recettes_by_ids(ids)

    # On construit un dictionnaire {id_recette: Recette} pour un accès rapide dans le template.
    # Ce mapping permet d’écrire dans Jinja : recette_map[item.id_recette].nom_recette
    recette_map = build_recette_map(recettes)

    # On envoie au template :
    # - selected_data : la sélection Pydantic (quantités, id_recette, etc.)
    # - recette_map   : les objets Recette complets (nom, type, robot, etc.)
    # Le template combine les deux pour afficher une ligne complète par recette sélectionnée.
    return render_template(
        "select_recettes/selection_result.html",
        selected_data=selected_data_pydantic.recette_selection_items,
        recette_map=recette_map,
    )


# ----------------------------------------------------------------------
# Génération : création de la liste des courses
# ----------------------------------------------------------------------
list_course_bp = Blueprint("list_courses", __name__, url_prefix="/list_courses")

@list_course_bp.route("/generate", methods=["GET", "POST"])
def generate():

    # 1. Récupération de la sélection Pydantic
    # Le service stocke la sélection courante dans _input_model.
    # Si rien n'est encore sélectionné → on obtient une liste vide.
    # selected_data_pydantic: ListeRecetteSelection = (
    #     serviceListeCourse._input_model
    #     or ListeRecetteSelection(recette_selection_items=[])
    # )
    selected_data_pydantic: ListeRecetteSelection = load_selection_from_redis()
    
    # Si l'utilisateur soumet le formulaire (POST)
    if request.method == "POST":

        # Si aucune recette n'a été sélectionnée, on empêche la génération.
        if not selected_data_pydantic.recette_selection_items:
            flash("Aucune liste disponible. Veuillez sélectionner des recettes.", "warning")
            return redirect(url_for("recettes.index"))

        try:
            # 2. Appel du pipeline métier
            # Le pipeline prend en entrée une liste de RecetteSelection
            # et renvoie un modèle Pydantic contenant la liste de courses générée.
            # results = pipeline(selected_data_pydantic.recette_selection_items)
            results: ListeCourse = pipeline_liste_course(selected_data_pydantic)

            # 4. Enregistrement en base
            # On ouvre une session DB et on insère le résultat du pipeline.
            # results.model_dump() convertit le modèle Pydantic en dict.
            with get_db() as db:
                course_crud.create(db, results.model_dump())

            # Message de succès et redirection vers la page de génération
            flash("Liste de course générée et enregistrée.", "success")
            return redirect(url_for("list_courses.generate"))

        except Exception as e:
            # Gestion d'erreur : on affiche un message à l'utilisateur
            flash(f"Erreur lors de la génération : {e}", "danger")

    # ------------------------------------------------------------------
    # GET : afficher le dernier résultat stocké dans Redis
    # ------------------------------------------------------------------
    # workflow_id = current_app.config["WORKFLOW_ID"]
    # raw = redis_client.get(f"liste_course:{workflow_id}:output")
    user_id = request.cookies.get("user_id")
    raw = redis_client.get(f"courses:{user_id}:output")

    results = None
    if raw:
        results = ListeCourse.model_validate_json(raw)

    return render_template(
        "generate_courses/detail.html",
        results=results,
    )
    
    # return render_template(
    #     "generate_courses/detail.html",
    #     results=serviceListeCourse._output_model,
    # )

