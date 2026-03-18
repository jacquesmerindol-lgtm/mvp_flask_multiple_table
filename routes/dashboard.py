from flask import Blueprint, render_template

from database import get_db
from models import Recette, Course, Livre
from sqlalchemy import desc
from sqlalchemy.orm import joinedload, load_only

# Blueprint exposé sous le nom `dashboard_bp` (utilisé dans main.py pour l’enregistrement)
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
def index():
    """Tableau de bord : recettes + dernières listes de courses."""
    with get_db() as db:
        recettes = (
            db.query(Recette)
            .options(
                load_only(Recette.id_recette, Recette.nom_recette, Recette.type_recette),
                joinedload(Recette.livre).load_only(Livre.nom_livre, Livre.numero_livre, Livre.nom_robot),
            )
            .order_by(Recette.nom_recette)
            .all()
        )

        last_courses = (
            db.query(Course)
            .options(load_only(Course.id_course, Course.date_liste_course, Course.liste_recette))
            .order_by(desc(Course.date_liste_course))
            .limit(3)
            .all()
        )

    return render_template(
        "dashboard.html",
        recettes=recettes,
        last_courses=last_courses,
    )
