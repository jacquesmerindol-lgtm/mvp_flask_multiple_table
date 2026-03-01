from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    SECRET_KEY: str
    DATABASE_URL: str

    ROBOTS_LIST: list[str] = ["Companion", "Cookeo", "Robot Chef X"]
    RECETTE_TYPES: list[str] = [
        "Entree",
        "Soupe",
        "Aperitif",
        "Plat",
        "Poisson",
        "Legume",
        "Dessert",
        "Autres"
    ]
    PERIODES_LIST: list[str] = [
        "janvier", "fevrier", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "decembre"
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
