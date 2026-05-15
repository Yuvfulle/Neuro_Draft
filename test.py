import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
from sklearn.feature_extraction import DictVectorizer
import pandas as pd
import numpy as np
import joblib

def vector_from_bitmask(radiant_mask, dire_mask, avg_rank_tier):
    radiant = sorted(radiant_mask.strip("[]").replace(" ","").split(","), key=int)
    dire = sorted(dire_mask.strip("[]").replace(" ","").split(","), key=int)
    bucket = "low"
    if avg_rank_tier > 64:
        bucket = "high"
    elif avg_rank_tier > 48:
        bucket = "high_mid"
    elif avg_rank_tier > 32:
        bucket = "mid"
    elif avg_rank_tier > 16:
        bucket = "low_mid"
    feats = {}
    feats["avg_rank_tier"] = float(avg_rank_tier)
    feats[f"rank_{bucket}"] = 1
    for r in radiant:
        feats[f"R_{r}"] = 1
    for d in dire:
        feats[f"D_{d}"] = 1
    for i in range(5):
        for j in range(i + 1, 5):
            feats[f"Rpair_{radiant[i]}_{radiant[j]}"] = 1
            feats[f"Dpair_{dire[i]}_{dire[j]}"] = 1
    for r in radiant:
        for d in dire:
            feats[f"RvD_{r}_{d}"] = 1
    return feats

data = pd.read_csv("NewMLDotaDB.csv")
data.columns = ['match_id', 'radiant_win', 'avg_rank_tier', 'radiant_team', 'dire_team']

x_dict = []
y = []
for row in data.itertuples(index=False):
    x_dict.append(vector_from_bitmask(
        row.radiant_team,
        row.dire_team,
        row.avg_rank_tier
    ))
    y.append(int(row.radiant_win))
Y = np.array(y)

X_train_raw, X_test_raw, Y_train, Y_test = train_test_split(
    x_dict, Y, test_size=0.2, random_state=67, stratify=Y
)

X_train_aug = []
Y_train_aug = []
for feats, win in zip(X_train_raw, Y_train):
    X_train_aug.append(feats)
    Y_train_aug.append(win)
    mirrored_feats = {}
    for k, v in feats.items():
        if k.startswith("R_"):
            mirrored_feats[k.replace("R_", "D_")] = v
        elif k.startswith("D_"):
            mirrored_feats[k.replace("D_", "R_")] = v
        elif k.startswith("Rpair_"):
            mirrored_feats[k.replace("Rpair_", "Dpair_")] = v
        elif k.startswith("Dpair_"):
            mirrored_feats[k.replace("Dpair_", "Rpair_")] = v
        else:
            mirrored_feats[k] = v
    X_train_aug.append(mirrored_feats)
    Y_train_aug.append(1 - win)

vectorizer = DictVectorizer(sparse=True)
X_train = vectorizer.fit_transform(X_train_aug)
X_test = vectorizer.transform(X_test_raw)

print("data is done, processing...")

md = xgb.XGBClassifier(
    n_estimators=10000,
    max_depth=3,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.5,
    reg_lambda=2.0,
    min_child_weight=5,
    eval_metric='logloss',
    early_stopping_rounds=100,
    random_state=67,
    tree_method='hist',
    device='cuda'
)

md.fit(
    X_train,
    Y_train_aug,
    eval_set=[(X_test, Y_test)],
    verbose=100
)

pred_y = md.predict(X_test)
proba_y = md.predict_proba(X_test)

print("accuracy: ", accuracy_score(Y_test, pred_y))
print("logloss: ", log_loss(Y_test, proba_y))
print(f"best iteration: {md.best_iteration}")

joblib.dump(md, "dota_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
print("ends")