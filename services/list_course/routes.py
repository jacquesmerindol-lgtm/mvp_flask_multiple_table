from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from database import get_db
from services.list_course.pipeline import pipeline
from crud import course_crud   

from services.list_course.logic import build_selection_pydantic

from services.list_course.crud import (
    get_recettes_filtered,
    get_recettes_by_ids,
)

from services.list_course.logic import build_recette_map

from services.service_instance import serviceListeCourse
from services.list_course.schema import RecetteSelection

# ----------------------------------------------------------------------
# Sélection : ajout de recettes à la sélection (avec addition des quantités)
# ----------------------------------------------------------------------

ingredients_bp = Blueprint("recettes_ui", __name__, url_prefix="/ingredients")

@ingredients_bp.route("/select", methods=["GET", "POST"])
def select_ui():
    # ----------------------------------------------------------------------
    # POST : ajout de recettes à la sélection (avec addition des quantités)
    # ----------------------------------------------------------------------
    if request.method == "POST":
        # getlist() renvoie toujours une liste ; C’est la méthode correcte pour gérer des sélections multiples. renvoie une liste de strings
        selected_ids = request.form.getlist("selected_recettes")

        # Si aucune case cochée → ne rien modifier
        if not selected_ids:
            return redirect(url_for("recettes_ui.select_ui"))

        # On part de la sélection existante
        selected_data_pydantic: list[RecetteSelection] = serviceListeCourse._input_model or []

        # Convertir en dict temporaire pour faciliter l’addition
        selected_data = {item.id_recette: item.nb_recette for item in selected_data_pydantic}

        # Ajout / addition des quantités
        for rid in selected_ids:
            nb_new = int(request.form.get(f"nb_recette_{rid}", 1))

            if rid in selected_data:
                # selected_data[rid_int]["nb_recette"] += nb_new
                selected_data[rid] += nb_new
            else:
                # selected_data[rid_int] = {"nb_recette": nb_new}
                selected_data[rid] = nb_new

        # Reconstruire la liste Pydantic propre
        selected_data_pydantic = build_selection_pydantic(selected_data)

        # Sauvegarde après transformation en list[RecetteSelection]
        serviceListeCourse._input_model = selected_data_pydantic

        # Rechargement des recettes pour affichage
        ids = [item.id_recette for item in selected_data_pydantic]
        recettes = get_recettes_by_ids(ids)
        recette_map = build_recette_map(recettes)

        return render_template(
            "select_recettes/selection_result.html",
            selected_data=selected_data_pydantic,
            recette_map=recette_map,
        )

    # ----------------------------------------------------------------------
    # GET : affichage + filtres + persistance de la sélection
    # ----------------------------------------------------------------------
    # Récupération de la sélection courante
    selected_data_pydantic = serviceListeCourse._input_model

    # Lecture des filtres envoyés dans l’URL
    f_periode = request.args.get("periode")
    f_robot = request.args.get("robot")
    f_nom = request.args.get("nom")
    f_type = request.args.get("type")

    # Récupération des recettes filtrées
    rows = get_recettes_filtered(
        periode=f_periode,
        robot=f_robot,
        nom_recette=f_nom,
        type_recette=f_type,
    )

    # Construction des listes de filtres disponibles
    all_periodes = sorted({p for r in rows for p in r.periode_recettes})
    all_robots = sorted({r.nom_robot for r in rows})
    all_types = sorted({r.type_recette for r in rows})

    # 🔥 Construire un map lisible pour la sélection existante
    recette_map = {}
    if selected_data_pydantic:
        # extraire les IDs
        ids = [item.id_recette for item in selected_data_pydantic]
        # charger les recettes SQLAlchemy correspondantes
        recettes = get_recettes_by_ids(ids)
        # construire un mapping lisible
        recette_map = build_recette_map(recettes)
        # Ce mapping est typiquement :
        # {
        #     "1": Recette(...),
        #     "5": Recette(...),
        #     "8": Recette(...),
        # }

    # Envoi des données au template
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
        selected_data=selected_data_pydantic,
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

    selected_data_pydantic: list[RecetteSelection] = serviceListeCourse._input_model or []
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
            selected_data_pydantic = [
                item for item in selected_data_pydantic
                if item.id_recette != rid_to_delete
            ]

            # On met à jour le modèle interne du service.
            serviceListeCourse._input_model = selected_data_pydantic

            # On recharge la page pour afficher la liste mise à jour.
            return redirect(url_for("recettes_ui.update_selection"))


        # --- MISE À JOUR DES QUANTITÉS POUR CHAQUE RECETTE ---

        updated_list = []

        # On parcourt chaque recette sélectionnée.
        for item in selected_data_pydantic:

            # On récupère la nouvelle quantité envoyée par le formulaire.
            # Le champ a name="nb_recette_<id>"
            new_value = request.form.get(f"nb_recette_{item.id_recette}")
            
            if new_value:
                # On met à jour l’objet Pydantic existant.
                # Pas de reconstruction → on garde les autres champs intacts.
                item.nb_recette = int(new_value)

            # On ajoute l’objet (modifié ou non) à la liste mise à jour.
            updated_list.append(item)

        # On sauvegarde la nouvelle liste dans le service.
        # (selected_data_pydantic et updated_list pointent sur les mêmes objets)
        serviceListeCourse._input_model = selected_data_pydantic

        # On recharge la page pour afficher les nouvelles quantités.
        return redirect(url_for("recettes_ui.update_selection"))


    # --- GET : affichage de la sélection actuelle ---

    # On extrait uniquement les identifiants des recettes sélectionnées.
    # selected_data_pydantic est une liste de RecetteSelection (modèles Pydantic).
    ids = [item.id_recette for item in selected_data_pydantic]

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
        selected_data=selected_data_pydantic,
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
    selected_data: list[RecetteSelection] = serviceListeCourse._input_model or []

    # Si l'utilisateur soumet le formulaire (POST)
    if request.method == "POST":

        # Si aucune recette n'a été sélectionnée, on empêche la génération.
        if not selected_data:
            flash("Aucune liste disponible. Veuillez sélectionner des recettes.", "warning")
            return redirect(url_for("recettes.index"))

        try:
            # 2. Appel du pipeline métier
            # Le pipeline prend en entrée une liste de RecetteSelection
            # et renvoie un modèle Pydantic contenant la liste de courses générée.
            results = pipeline(selected_data)

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

    # GET → affichage de la page de génération
    # On affiche simplement le dernier résultat généré (stocké dans _output_model)
    return render_template(
        "generate_courses/detail.html",
        results=serviceListeCourse._output_model,
    )

