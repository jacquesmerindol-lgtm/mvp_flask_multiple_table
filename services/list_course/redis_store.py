from app.redis_client import redis_client

from services.schema import ListeCourse, ListeRecetteSelection


def _redis_key(user_id: str | None, suffix: str) -> str:
    return f"courses:{user_id}:{suffix}"


def get_list_course_selection(user_id: str | None) -> ListeRecetteSelection:
    if not user_id:
        return ListeRecetteSelection(recette_selection_items=[])

    raw = redis_client.get(_redis_key(user_id, "selection"))
    if not raw:
        return ListeRecetteSelection(recette_selection_items=[])

    return ListeRecetteSelection.model_validate_json(raw)


def save_list_course_selection(user_id: str | None, selection: ListeRecetteSelection) -> None:
    if not user_id:
        return

    redis_client.set(
        _redis_key(user_id, "selection"),
        selection.model_dump_json(),
    )


def save_list_course_input(user_id: str | None, input_data: ListeRecetteSelection) -> None:
    if not user_id:
        return

    redis_client.set(
        _redis_key(user_id, "input"),
        input_data.model_dump_json(),
    )


def save_list_course_output(user_id: str | None, output: ListeCourse) -> None:
    if not user_id:
        return

    redis_client.set(
        _redis_key(user_id, "output"),
        output.model_dump_json(),
    )


def get_list_course_output(user_id: str | None) -> ListeCourse | None:
    if not user_id:
        return None

    raw = redis_client.get(_redis_key(user_id, "output"))
    if not raw:
        return None

    return ListeCourse.model_validate_json(raw)
