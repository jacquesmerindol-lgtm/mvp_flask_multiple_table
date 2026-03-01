# services/ocr/utils.py

from database import get_db
from models import Livre

def get_livres_choices():
    """
    Renvoie une liste de tuples :
    [(id_livre, "numéro — nom"), ...]
    Les livres sont triés par numéro puis par nom.
    """
    with get_db() as db:
        livres = db.query(Livre).order_by(Livre.numero_livre, Livre.nom_livre).all()
        return [
            (l.id_livre, f"{l.numero_livre or 'N/A'} — {l.nom_livre}")
            for l in livres
        ]
