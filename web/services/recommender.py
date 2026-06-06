from collections import namedtuple

from web.services import data_service, model_service


DEFAULT_TOP_K = 30

W_WINRATE = 1.0
W_SYNERGY = 0.5
W_MATCHUP = 0.5
W_COUNTER = 0.5

Cand = namedtuple("Cand", "id role score")

class RecommendationError(Exception):
    pass


def _role_label(rid):
    return data_service.ROLE_NAMES.get(rid, rid)


def _split_for_side(side, ours, theirs):
    return (ours, theirs) if side == "radiant" else (theirs, ours)


def _candidates(banned, allies, enemies, ally_roles):

    used = set(allies) | set(enemies) | set(banned)
    used_roles = set(ally_roles)

    out = []
    for hid in data_service.all_hero_ids():
        if hid in used:
            continue
        free = next((r for r in data_service.hero_roles(hid) if r not in used_roles), None)
        if free is not None:
            out.append((hid, free))
    return out




def _score_winrate(rank_group, cands):
    return [Cand(hid, role, data_service.get_winrate(hid, rank_group) / 100.0)
            for hid, role in cands]


def _score_synergy(rank_group, cands, ally):
    out = []
    for hid, role in cands:
        wr = data_service.get_winrate(hid, rank_group) / 100.0
        syn = data_service.get_synergy(hid, ally, rank_group) or 0.0
        out.append(Cand(hid, role, wr + syn / 100.0))
    return out


def _avg(values, default):
    known = [v for v in values if v is not None]
    return sum(known) / len(known) if known else default


def _score_uncomp(rank_group, cands, allies, enemies):
    out = []
    for hid, role in cands:
        wr = data_service.get_winrate(hid, rank_group) / 100.0
        avg_syn = _avg((data_service.get_synergy(hid, a, rank_group) for a in allies), 0.0) / 100.0

        if enemies:
            avg_match = _avg((data_service.get_matchup(hid, e, rank_group) for e in enemies), 50.0) / 100.0
            avg_risk = sum(data_service.get_counter_risk(hid, e, rank_group) for e in enemies) / len(enemies) / 100.0
        else:
            avg_match = 0.5
            avg_risk = 0.0

        score = (W_WINRATE * wr
                 + W_SYNERGY * avg_syn
                 + W_MATCHUP * (avg_match - 0.5)
                 - W_COUNTER * avg_risk)

        out.append(Cand(hid, role, score))
    return out


def _score_model(side, cands, allies, enemies, rank_tier):
    rows = [_split_for_side(side, allies + [hid], enemies) for hid, xz_lol in cands]

    probs = model_service.predict_package(rows, avg_rank_tier=rank_tier)

    out = []
    for i in range(len(cands)):
        hid, role = cands[i]
        p = probs[i]
        score = p if side == "radiant" else 1.0 - p
        out.append(Cand(hid, role, score))
    return out


def _score_minimax(side, rank_group, cands, allies, enemies, rank_tier, banned):
    our_top = sorted(_score_uncomp(rank_group, cands, allies, enemies),key=lambda c: c.score,reverse=True,)

    used = set(allies) | set(enemies) | set(banned)
    enemy_pool = [
        h for h in data_service.all_hero_ids()
        if h not in used
    ]

    out = []
    for c in our_top:
        replies = [e for e in enemy_pool if e != c.id]
        rows = [_split_for_side(side, allies + [c.id], enemies + [e]) for e in replies]
        probs = model_service.predict_package(rows, avg_rank_tier=rank_tier)
        worst = min(probs) if side == "radiant" else 1.0 - max(probs)
        out.append(Cand(c.id, c.role, worst))
    return out





def _build_item(hid, role, raw, side, radiant_ids, dire_ids):
    role_ids = data_service.hero_roles(hid)
    return {
        "id": hid,
        "name": data_service.hero_name(hid),
        "score": round(max(0.0, min(100.0, raw * 100.0)), 1),
        "raw_score": round(raw, 4),
        "role_ids": role_ids,
        "roles": [_role_label(r) for r in role_ids],
        "recommended_role_id": role,
        "recommended_role": _role_label(role) if role else "",
        "target_side": side,
        "radiant_team": [data_service.hero_name(h) for h in radiant_ids],
        "dire_team": [data_service.hero_name(h) for h in dire_ids],
    }


def _full_draft(radiant, dire, rank_tier, side):
    p = model_service.predict_radiant_win(radiant, dire, rank_tier)
    team_p = p if side == "radiant" else 1.0 - p
    return {
        "mode": "draft_score",
        "team_score": round(team_p * 100.0, 1),
        "radiant_score": round(p * 100.0, 1),
        "radiant_team": [data_service.hero_name(h) for h in radiant],
        "dire_team": [data_service.hero_name(h) for h in dire],
        "score_note": "P(Radiant win) от модели",
    }



def recommend(ally_picks, ally_roles, enemy_picks,banned, side, rank_tier):
    side = (side or "radiant").lower()
    if side not in ("radiant", "dire"):
        raise RecommendationError("side должен быть radiant или dire.")

    allies = [int(h) for h in ally_picks]
    enemies = [int(h) for h in enemy_picks]
    banned_ids = [int(h) for h in banned]

    for hid in allies + enemies + banned_ids:
        if not data_service.hero_exists(hid):
            raise RecommendationError(f"Героя с id={hid} нет в словаре.")

    n = len(allies) + len(enemies)
    if n == 10:
        radiant_ids, dire_ids = _split_for_side(side, allies, enemies)
        return _full_draft(radiant_ids, dire_ids, rank_tier, side)

    rank_group = data_service.rank_group(rank_tier)
    cands = _candidates(banned_ids, allies, enemies, ally_roles)
    if not cands:
        raise RecommendationError("Нет подходящих кандидатов: все роли заняты.")

    if n == 0:
        scored = _score_winrate(rank_group, cands)
    elif n == 1 and allies:
        scored = _score_synergy(rank_group, cands, allies[0])
    elif 1 <= n <= 7:
        scored = _score_uncomp(rank_group, cands, allies, enemies)
    elif n == 8:
        scored = _score_minimax(side, rank_group, cands, allies, enemies, rank_tier, banned_ids)
    elif n == 9:
        scored = _score_model(side, cands, allies, enemies, rank_tier)

    scored.sort(key=lambda c: c.score, reverse=True)
    scored = scored[:DEFAULT_TOP_K]

    items = []
    for c in scored:
        rv, dv = _split_for_side(side, allies + [c.id], enemies)
        items.append(_build_item(c.id, c.role, c.score, side, rv, dv))

    return {
        "recommendations": items,
        "top_pool": len(items),
        "draft_status": {"summary": f"Стадия {n}/10. Кандидатов: {len(cands)}."},
    }
