from .debug_generic import make_debug_blueprint
from crud import livre_crud, recette_crud

debug_livres_bp = make_debug_blueprint("livres", livre_crud)
debug_recettes_bp = make_debug_blueprint("recettes", recette_crud)

__all__ = [
    "debug_livres_bp",
    "debug_recettes_bp",
]
