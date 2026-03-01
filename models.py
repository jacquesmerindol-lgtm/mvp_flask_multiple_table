from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship

from database import Base


class Livre(Base):
    __tablename__ = "livre"

    id_livre = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    position = Column(Integer, default=0)
    nom_livre = Column(String(255), nullable=False, unique=True)
    numero_livre = Column(String(64), nullable=True)
    periode_recettes = Column(JSON, nullable=False)  # list[str]
    nom_robot = Column(String(100), nullable=False)

    __table_args__ = (
        Index("idx_livre_nom_unique", "nom_livre", unique=True),
    )

    # ❗ Aucun cascade → ON DELETE RESTRICT respecté
    recettes = relationship("Recette", back_populates="livre")
    __unique_fields__ = ["nom_livre"]


class Recette(Base):
    __tablename__ = "recette"

    id_recette = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    position = Column(Integer, default=0)
    nom_recette = Column(String(255), nullable=False, unique=True)
    type_recette = Column(String(30), nullable=False)
    nombre_personnes = Column(Integer, CheckConstraint("nombre_personnes >= 0"), nullable=False)
    duree_preparation = Column(Integer, CheckConstraint("duree_preparation >= 0"), default=0)
    duree_cuisson = Column(Integer, CheckConstraint("duree_cuisson >= 0"), default=0)
    duree_repos = Column(Integer, CheckConstraint("duree_repos >= 0"), default=0)
    liste_ingredients = Column(JSON)  # list[dict]
    instructions = Column(Text, nullable=True)
    astuce = Column(Text, nullable=True)

    id_livre_reference = Column(
        Integer,
        ForeignKey("livre.id_livre", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )

    __table_args__ = (
        Index("idx_recette_id_livre", "id_livre_reference"),
    )

    livre = relationship("Livre", back_populates="recettes")
    __unique_fields__ = ["nom_recette"]
