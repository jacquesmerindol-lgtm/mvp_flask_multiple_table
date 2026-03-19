import json
from app.redis_client import redis_client
from services.schema import OCRResults, Recette


def _redis_key(user_id: str | None, prefix: str, suffix: str) -> str:
    return f"{prefix}:{user_id}:{suffix}"


def get_ocr_output(user_id: str | None) -> OCRResults | None:
    if not user_id:
        return None

    raw = redis_client.get(_redis_key(user_id, "ocr", "output"))
    if not raw:
        return None
    return OCRResults.model_validate_json(raw)


def save_ocr_input(user_id: str | None, paths: list[str]) -> None:
    if not user_id:
        return

    redis_client.set(
        _redis_key(user_id, "ocr", "input"),
        json.dumps(paths, ensure_ascii=False),
    )


def save_ocr_output(user_id: str | None, results: OCRResults) -> None:
    if not user_id:
        return

    redis_client.set(
        _redis_key(user_id, "ocr", "output"),
        results.model_dump_json(),
    )


def get_ocr_structuration_output(user_id: str | None) -> list[Recette] | None:
    if not user_id:
        return None

    raw = redis_client.get(_redis_key(user_id, "structuration", "output"))
    if not raw:
        return None

    data = json.loads(raw)
    return [Recette(**item) for item in data]


def save_ocr_structuration_input(user_id: str | None, ocr_results: OCRResults) -> None:
    if not user_id:
        return

    redis_client.set(
        _redis_key(user_id, "structuration", "input"),
        ocr_results.model_dump_json(),
    )


def save_ocr_structuration_output(user_id: str | None, structured_items: list[Recette]) -> None:
    if not user_id:
        return

    payload = [item.model_dump(mode="json") for item in structured_items]
    redis_client.set(
        _redis_key(user_id, "structuration", "output"),
        json.dumps(payload, ensure_ascii=False),
    )


def save_ocr_selected_livre(user_id: str | None, livre_id: int) -> None:
    if not user_id:
        return

    redis_client.set(
        _redis_key(user_id, "ocr", "selected_livre"),
        str(livre_id),
    )


def get_ocr_selected_livre(user_id: str | None) -> int | None:
    if not user_id:
        return None

    raw = redis_client.get(_redis_key(user_id, "ocr", "selected_livre"))
    if not raw:
        return None
    return int(raw)
