import json
from flask import request
from app.redis_client import redis_client
from services.schema import OCRResults, Recette


def load_ocr_from_redis() -> OCRResults | None:
    user_id = request.cookies.get("user_id")
    raw = redis_client.get(f"ocr:{user_id}:output")
    if not raw:
        return None
    return OCRResults.model_validate_json(raw)


def load_structuration_from_redis() -> list[Recette] | None:
    user_id = request.cookies.get("user_id")
    raw = redis_client.get(f"structuration:{user_id}:output")
    if not raw:
        return None

    data = json.loads(raw)
    return [Recette(**item) for item in data]


def save_structuration_to_redis(structured_items: list[Recette]) -> None:
    user_id = request.cookies.get("user_id")
    payload = [item.model_dump(mode="json") for item in structured_items]
    redis_client.set(
        f"structuration:{user_id}:output",
        json.dumps(payload, ensure_ascii=False)
    )


def save_selected_livre_to_redis(livre_id: int) -> None:
    user_id = request.cookies.get("user_id")
    redis_client.set(f"ocr:{user_id}:selected_livre", str(livre_id))


def load_selected_livre_from_redis() -> int | None:
    user_id = request.cookies.get("user_id")
    raw = redis_client.get(f"ocr:{user_id}:selected_livre")
    if not raw:
        return None
    return int(raw)
