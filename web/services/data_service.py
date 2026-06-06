import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

ROLE_NAMES = {
    "carry": "Carry",
    "mid": "Mid",
    "offlane": "Offlane",
    "soft_support": "Soft Support",
    "hard_support": "Hard Support",
}


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

_roles_raw = _load_json(DATA_DIR / "hero_roles.json")
_aliases_raw = _load_json(DATA_DIR / "hero_aliases.json")

_heroes = {
    int(sngl["id"]): {"name": sngl["name"], "winrates": sngl["winrates"]}
    for sngl in _load_json(DATA_DIR / "hero_winrates_by_rank.json")
}

_synergy_index = {
    (int(sngl["hero_id"]), int(sngl["ally_hero_id"])): sngl["synergies"]
    for sngl in _load_json(DATA_DIR / "hero_synergies_by_rank.json")
}

_counter_index = {
    (int(sngl["hero_id"]), int(sngl["against_hero_id"])): sngl["winrates"]
    for sngl in _load_json(DATA_DIR / "hero_counters_by_rank.json")
}

def rank_group(avg_rank_tier):
    rank = int(avg_rank_tier)
    if rank > 64: return "rank_high"
    if rank > 48: return "rank_high_mid"
    if rank > 32: return "rank_mid"
    if rank > 16: return "rank_low_mid"
    return "rank_low"

def all_hero_ids():
    return list(_heroes.keys())


def hero_exists(hero_id):
    return int(hero_id) in _heroes


def hero_name(hero_id):
    return _heroes[int(hero_id)]["name"]


def hero_roles(hero_id):
    return _roles_raw.get(str(hero_id), [])


def get_all_heroes():
    return [
        {
            "id": hid,
            "name": _heroes[hid]["name"],
            "roles": hero_roles(hid),
            "aliases": _aliases_raw.get(str(hid), []),
        }
        for hid in sorted(_heroes)
    ]


def get_role_choices():
    return [{"id": rid, "name": name} for rid, name in ROLE_NAMES.items()]


def get_winrate(hero_id, rank_group):
    return float(_heroes[int(hero_id)]["winrates"][rank_group])


def get_synergy(h1, h2, rank_group):
    syn = _synergy_index.get((int(h1), int(h2)))
    if not syn:
        return None
    return float(syn.get(rank_group, 0.0))


def get_matchup(hero_id, enemy_id, rank_group):
    return float(_counter_index[(int(hero_id), int(enemy_id))].get(rank_group, 50.0))


def get_counter_risk(hero_id, enemy_id, rank_group):
    return max(0.0, 50.0 - get_matchup(hero_id, enemy_id, rank_group))
