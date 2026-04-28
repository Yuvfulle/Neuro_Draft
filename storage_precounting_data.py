import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction import DictVectorizer
import joblib
import json
import scipy.sparse as sp
from itertools import combinations

with open("hero_winrates_ranks_1_7.json", "r", encoding="utf-8") as f:
    raw_wr = json.load(f)

hero_winrates = {}
for hero in raw_wr:
    hid = str(hero["id"])
    hero_winrates[hid] = {
        rank: val / 100.0
        for rank, val in hero["winrates"].items()
    }

def get_hero_wr(hero_id, rank_bucket):
    return hero_winrates.get(hero_id, {}).get(rank_bucket, 0.5)

def vector_from_bitmask(radiant_mask, dire_mask, avg_rank_tier):
    radiant = sorted(radiant_mask.strip("[]").replace(" ", "").split(","), key=int)
    dire = sorted(dire_mask.strip("[]").replace(" ", "").split(","), key=int)

    bucket = ""
    if avg_rank_tier > 64:
        bucket = "rank_high"
    elif avg_rank_tier > 48:
        bucket = "rank_high_mid"
    elif avg_rank_tier > 32:
        bucket = "rank_mid"
    elif avg_rank_tier > 16:
        bucket = "rank_low_mid"
    else:
        bucket = "rank_low"

    feats = {}
    feats["avg_rank_tier"] = float(avg_rank_tier)
    feats[f"{bucket}"] = 1

    for r in radiant:
        feats[f"R_{r}"] = 1
        feats[f"R_{r}_{bucket}"] = 1
    for d in dire:
        feats[f"D_{d}"] = 1
        feats[f"D_{d}_{bucket}"] = 1

    r_wrs = [get_hero_wr(r, bucket) for r in radiant]
    d_wrs = [get_hero_wr(d, bucket) for d in dire]

    feats["radiant_avg_wr"] = float(np.mean(r_wrs))
    feats["dire_avg_wr"] = float(np.mean(d_wrs))
    feats["wr_diff"] = feats["radiant_avg_wr"] - feats["dire_avg_wr"]
    feats["radiant_min_wr"] = float(np.min(r_wrs))
    feats["dire_min_wr"] = float(np.min(d_wrs))
    feats["radiant_max_wr"] = float(np.max(r_wrs))
    feats["dire_max_wr"] = float(np.max(d_wrs))

    r_pair_wrs = [get_pair_wr(r1, r2, bucket) for r1, r2 in combinations(radiant, 2)]
    d_pair_wrs = [get_pair_wr(d1, d2, bucket) for d1, d2 in combinations(dire, 2)]

    feats["radiant_avg_pair_wr"] = float(np.mean(r_pair_wrs))
    feats["dire_avg_pair_wr"] = float(np.mean(d_pair_wrs))
    feats["pair_wr_diff"] = feats["radiant_avg_pair_wr"] - feats["dire_avg_pair_wr"]

    matchup_wrs = [get_matchup_wr(r, d, bucket) for r in radiant for d in dire]
    feats["avg_matchup_wr"] = float(np.mean(matchup_wrs))

    r_triple_wrs = [get_triple_wr(h1, h2, h3, bucket) for h1, h2, h3 in combinations(radiant, 3)]
    d_triple_wrs = [get_triple_wr(h1, h2, h3, bucket) for h1, h2, h3 in combinations(dire, 3)]

    feats["radiant_avg_triple_wr"] = float(np.mean(r_triple_wrs))
    feats["dire_avg_triple_wr"]    = float(np.mean(d_triple_wrs))
    feats["triple_wr_diff"]        = feats["radiant_avg_triple_wr"] - feats["dire_avg_triple_wr"]

    feats["best_hero_wr_diff"] = max(r_wrs) - max(d_wrs)
    feats["worst_hero_wr_diff"] = min(r_wrs) - min(d_wrs)

    feats["radiant_std_wr"] = float(np.std(r_wrs))
    feats["dire_std_wr"]    = float(np.std(d_wrs))

    for i, r in enumerate(radiant):
        for j, d in enumerate(dire):
            feats[f"matchup_wr_{i}_{j}"] = get_matchup_wr(r, d, bucket)

    for i in range(5):
        for j in range(i + 1, 5):
            feats[f"Rpair_{radiant[i]}_{radiant[j]}"] = 1
            feats[f"Dpair_{dire[i]}_{dire[j]}"] = 1

    #for r in radiant:
    #    for d in dire:
    #        feats[f"RvD_{r}_{d}"] = 1

    return feats

def mirror_feats(feats, win):
    mirrored = {}
    for k, v in feats.items():
        if k.startswith("R_"): mirrored[k.replace("R_", "D_", 1)] = v
        elif k.startswith("D_"): mirrored[k.replace("D_", "R_", 1)] = v
        elif k.startswith("Rpair_"): mirrored[k.replace("Rpair_", "Dpair_", 1)] = v
        elif k.startswith("Dpair_"): mirrored[k.replace("Dpair_", "Rpair_", 1)] = v
        elif k.startswith("RvD_"):
            parts = k.split("_")
            mirrored[f"RvD_{parts[2]}_{parts[1]}"] = v
        elif k.startswith("radiant_"): mirrored[k.replace("radiant_", "dire_", 1)] = v
        elif k.startswith("dire_"): mirrored[k.replace("dire_", "radiant_", 1)] = v
        elif k == "wr_diff": mirrored["wr_diff"] = -v
        elif k == "pair_wr_diff": mirrored["pair_wr_diff"] = -v
        elif k == "avg_matchup_wr": mirrored["avg_matchup_wr"] = 1.0 - v 
        elif k == "triple_wr_diff": mirrored["triple_wr_diff"] = -v
        elif k == "best_hero_wr_diff":  mirrored["best_hero_wr_diff"]  = -v
        elif k == "worst_hero_wr_diff": mirrored["worst_hero_wr_diff"] = -v
        elif k.startswith("matchup_wr_"):
            parts = k.split("_")  # matchup_wr_i_j
            mirrored[f"matchup_wr_{parts[3]}_{parts[2]}"] = 1.0 - v
        else: mirrored[k] = v
    return mirrored, 1 - win

pair_stats = {}   # {(h1, h2): [wins, total]}
matchup_stats = {}  # {(r, d): [wins, total]}  wins = radiant win
triple_stats = {}

def get_pair_wr(h1, h2, bucket):
    key = (min(h1, h2), max(h1, h2), bucket)
    stats = pair_stats.get(key)
    if stats is None or stats[1] < 50:
        return 0.5
    return stats[0] / stats[1]

def get_matchup_wr(r, d, bucket):
    stats = matchup_stats.get((r, d, bucket))
    if stats is None or stats[1] < 50:
        return 0.5
    return stats[0] / stats[1]

def get_triple_wr(h1, h2, h3, bucket):
    s = sorted([h1, h2, h3])
    key = (s[0], s[1], s[2], bucket)
    stats = triple_stats.get(key)
    if stats is None or stats[1] < 50:
        return 0.5
    return stats[0] / stats[1]

data = pd.read_csv("NewMLDotaDB.csv")
data.columns = ['match_id', 'radiant_win', 'avg_rank_tier', 'radiant_team', 'dire_team']

print("counting pair/matchup stats...")
for row in data.itertuples(index=False):
    radiant = sorted(row.radiant_team.strip("[]").replace(" ", "").split(","), key=int)
    dire = sorted(row.dire_team.strip("[]").replace(" ", "").split(","), key=int)
    win = int(row.radiant_win)

    avg_rank_tier = row.avg_rank_tier
    bucket = ""
    if avg_rank_tier > 64:
        bucket = "rank_high"
    elif avg_rank_tier > 48:
        bucket = "rank_high_mid"
    elif avg_rank_tier > 32:
        bucket = "rank_mid"
    elif avg_rank_tier > 16:
        bucket = "rank_low_mid"
    else:
        bucket = "rank_low"

    for h1, h2 in combinations(radiant, 2):
        key = (h1, h2, bucket)
        if key not in pair_stats:
            pair_stats[key] = [0, 0]
        pair_stats[key][0] += win # radiant win
        pair_stats[key][1] += 1

    for h1, h2 in combinations(dire, 2):
        key = (h1, h2, bucket)
        if key not in pair_stats:
            pair_stats[key] = [0, 0]
        pair_stats[key][0] += (1 - win)  # dire win
        pair_stats[key][1] += 1

    # r vs d
    for r in radiant:
        for d in dire:
            key = (r, d, bucket)
            if key not in matchup_stats:
                matchup_stats[key] = [0, 0]
            matchup_stats[key][0] += win   # r vs d
            matchup_stats[key][1] += 1

    for h1, h2, h3 in combinations(radiant, 3):
        key = (min(h1,h2,h3), sorted([h1,h2,h3])[1], max(h1,h2,h3), bucket)
        if key not in triple_stats:
            triple_stats[key] = [0, 0]
        triple_stats[key][0] += win
        triple_stats[key][1] += 1

    for h1, h2, h3 in combinations(dire, 3):
        key = (min(h1,h2,h3), sorted([h1,h2,h3])[1], max(h1,h2,h3), bucket)
        if key not in triple_stats:
            triple_stats[key] = [0, 0]
        triple_stats[key][0] += (1 - win)
        triple_stats[key][1] += 1

print("stats done.")

x_dict = []
y = []
total = len(data)
for i, row in enumerate(data.itertuples(index=False)):
    x_dict.append(vector_from_bitmask(row.radiant_team, row.dire_team, row.avg_rank_tier))
    y.append(int(row.radiant_win))
    if i % 100000 == 0:
        print(f"processing... {i}/{total}")
Y = np.array(y)

x_trainval, x_test_raw, y_trainval, y_test = train_test_split(
    x_dict, Y, test_size=0.15, random_state=67, stratify=Y
)
x_train_raw, x_calib_raw, y_train_raw, y_calib = train_test_split(
    x_trainval, y_trainval, test_size=0.176, random_state=67, stratify=y_trainval
)

x_train_aug = []
y_train_aug = []
for i, (feats, win) in enumerate(zip(x_train_raw, y_train_raw)):
    x_train_aug.append(feats)
    y_train_aug.append(win)
    m_feats, m_win = mirror_feats(feats, win)
    x_train_aug.append(m_feats)
    y_train_aug.append(m_win)
    if i % 100000 == 0:
        print(f"augmenting... {i}/{len(x_train_raw)}")
y_train_aug = np.array(y_train_aug)

vectorizer = DictVectorizer(sparse=True)
X_train = vectorizer.fit_transform(x_train_aug)
X_calib = vectorizer.transform(x_calib_raw)
X_test = vectorizer.transform(x_test_raw)

print(f"features: {X_train.shape[1]}, train: {X_train.shape[0]}")

# сохраняем всё
sp.save_npz("X_train.npz", X_train)
sp.save_npz("X_calib.npz", X_calib)
sp.save_npz("X_test.npz",  X_test)
np.save("y_train.npy", y_train_aug)
np.save("y_calib.npy", y_calib)
np.save("y_test.npy",  y_test)
joblib.dump(vectorizer, "vectorizer.pkl")
print("data saved.")