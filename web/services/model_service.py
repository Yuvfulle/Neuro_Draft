import pickle
from itertools import combinations
from pathlib import Path

from web.services import data_service


MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"


def _load_pickle(name):
    with open(MODELS_DIR / name, "rb") as f:
        return pickle.load(f)


_model = _load_pickle("dota_model.pkl")
_vectorizer = _load_pickle("vectorizer.pkl")


def _features(radiant, dire, avg_rank_tier):

    radiant = sorted(int(h) for h in radiant)
    dire = sorted(int(h) for h in dire)
    rank_group = data_service.rank_group(avg_rank_tier)

    feats = {"avg_rank_tier": float(avg_rank_tier), rank_group: 1}

    for r in radiant:
        feats[f"R_{r}"] = 1

    for d in dire:
        feats[f"D_{d}"] = 1

    for r1, r2 in combinations(radiant, 2):
        feats[f"Rpair_{r1}_{r2}"] = 1

    for d1, d2 in combinations(dire, 2):
        feats[f"Dpair_{d1}_{d2}"] = 1

    for r in radiant:

        for d in dire:
            feats[f"RvD_{r}_{d}"] = 1

    return feats


def predict_package(rows, avg_rank_tier):
    if isinstance(avg_rank_tier, list):
        ranks = avg_rank_tier
    else:
        ranks = [avg_rank_tier] * len(rows)

    feats = []

    for i in range(len(rows)):
        r, d = rows[i]
        rt = ranks[i]
        feats.append(_features(r, d, rt))

    for_model = _vectorizer.transform(feats)
    return _model.predict_proba(for_model)[:, 1].tolist()


def predict_radiant_win(radiant, dire, avg_rank_tier):
    if len(radiant) != 5 or len(dire) != 5:
        raise ValueError("predict_radiant_win expects 5v5.")
    return predict_package([(radiant, dire)], avg_rank_tier)[0]
