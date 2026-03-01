from flask import Flask, render_template

from config import get_settings
from database import Base, engine

# Blueprints
# from routes.debug_livres import debug_livres_bp
# from routes.debug_recettes import debug_recettes_bp
from routes import debug_livres_bp, debug_recettes_bp
from routes.livres import livres_bp
from routes.recettes import recettes_bp
from services.ocr.routes import bp as ocr_bp
# Importer les formulaires pour que render_form() fonctionne
import forms  # noqa: F401

from flask_bootstrap import Bootstrap5


def create_app():
    app = Flask(__name__)
    settings = get_settings()

    # Configuration
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["WTF_CSRF_ENABLED"] = True

    # Bootstrap-Flask
    from flask_bootstrap import Bootstrap
    Bootstrap5(app)

    # Création des tables
    Base.metadata.create_all(bind=engine)

    # Enregistrement des blueprints
    app.register_blueprint(livres_bp)
    app.register_blueprint(recettes_bp)
    app.register_blueprint(debug_livres_bp) 
    app.register_blueprint(debug_recettes_bp)
    app.register_blueprint(ocr_bp) # ← obligatoire

    # Page d'accueil
    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
