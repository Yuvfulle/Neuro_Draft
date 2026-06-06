import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from web.services import data_service, recommender


DRAFT_CONFIG = {
    "team_size": 5,
    "max_bans": 10,
    "visible_recommendations": 6,
    "default_top_pool": recommender.DEFAULT_TOP_K,
    "recommend_url": "/api/recommend/",
}


def home(request):
    return render(request, "home.html", {
        "heroes": data_service.get_all_heroes(),
        "roles": data_service.get_role_choices(),
        "config": DRAFT_CONFIG,
    })


def _read_json(request):
    return json.loads(request.body or b"{}")


def _int_list(payload, key):
    values = payload.get(key) or []
    if not isinstance(values, list):
        raise ValueError(f"Поле {key} должно быть списком.")
    try:
        return [int(v) for v in values]
    except (TypeError, ValueError):
        raise ValueError(f"В поле {key} ожидаются целые id героев.")


def _str_list(payload, key):
    values = payload.get(key) or []
    if not isinstance(values, list):
        raise ValueError(f"Поле {key} должно быть списком.")
    return [str(v) for v in values]


def _error(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)


@require_http_methods(["POST"])
def api_recommend(request):
    payload = _read_json(request)
    if payload is None:
        return _error("Невалидный JSON.")

    try:
        result = recommender.recommend(
            ally_picks=_int_list(payload, "ally_heroes"),
            ally_roles=_str_list(payload, "ally_roles"),
            enemy_picks=_int_list(payload, "enemy_heroes"),
            banned=_int_list(payload, "banned_heroes"),
            side=str(payload.get("side", "radiant")),
            rank_tier=payload.get("avg_rank_tier", 50),
        )
    except (ValueError, recommender.RecommendationError) as exc:
        return _error(str(exc))

    return JsonResponse(result)
