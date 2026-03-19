from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Livre, Recette, Course

T = TypeVar("T")


class CRUDGeneric(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model
        # Récupération propre de la clé primaire
        self.pk = self.model.__mapper__.primary_key[0]

    def get(self, db: Session, id_: int) -> Optional[T]:
        return db.query(self.model).filter(self.pk == id_).first()

    def get_all(self, db: Session) -> List[T]:
        return db.query(self.model).all()

    def create(self, db: Session, obj_in: dict) -> T:
        self.validate_unique_fields(db, obj_in)
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: T, obj_in: dict) -> T:
        self.validate_unique_fields(db, obj_in, exclude_id=getattr(db_obj, self.pk.key))

        for key, value in obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_restricted(self, db: Session, id_: int) -> bool:
        obj = self.get(db, id_)
        if not obj:
            return False
        try:
            db.delete(obj)
            db.commit()
            return True
        except IntegrityError:
            # ON DELETE RESTRICT déclenche une erreur SQL
            db.rollback()
            return False

    def delete_all_restricted(self, db: Session) -> int:
        # Suppression ligne par ligne pour respecter ON DELETE RESTRICT
        objs = db.query(self.model).all()
        count = 0
        for obj in objs:
            try:
                db.delete(obj)
                db.commit()
                count += 1
            except IntegrityError:
                db.rollback()
        return count
    
    def delete_cascade(self, db: Session, id_: int) -> bool:
        obj = self.get(db, id_)
        if not obj:
            return False

        db.delete(obj)
        db.commit()
        return True
    
    def delete_all_cascade(self, db: Session) -> int:
        count = db.query(self.model).delete()
        db.commit()
        return count

    def search_by_id(self, db: Session, id_: int) -> List[T]: 
        return db.query(self.model).filter(self.pk == id_).all()
    
    def exists(self, db: Session, field: str, value, exclude_id=None) -> bool:
        column = getattr(self.model, field, None)
        if column is None:
            raise AttributeError(f"Le modèle {self.model.__name__} n'a pas de champ '{field}'")

        query = db.query(self.model).filter(column == value)

        if exclude_id:
            query = query.filter(self.pk != exclude_id)

        return db.query(query.exists()).scalar()
    
    def validate_unique_fields(self, db: Session, obj_in: dict, exclude_id=None):
        unique_fields = getattr(self.model, "__unique_fields__", [])

        for field in unique_fields:
            if field in obj_in:
                if self.exists(db, field, obj_in[field], exclude_id=exclude_id):
                    raise ValueError(f"Le champ '{field}' doit être unique.")


# Instances spécifiques
livre_crud = CRUDGeneric(Livre)
recette_crud = CRUDGeneric(Recette)
course_crud = CRUDGeneric(Course)

