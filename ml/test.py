import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
from sklearn.feature_extraction import FeatureHasher
import pandas as pd
import numpy as np

import joblib

hasher = FeatureHasher(n_features=131072 , input_type='dict')

def vector_from_bitmask(radiant_mask , dire_mask):
    radiant = []
    dire = []
    for _ in range(5):
        bit = radiant_mask & -radiant_mask
        radiant.append(bit.bit_length()-1)
        radiant_mask ^= bit
    for _ in range(5):
        bit = dire_mask & -dire_mask
        dire.append(bit.bit_length()-1)
        dire_mask ^= bit

    combos_list = [] #unique list with heroes combos

    for r in radiant:
        combos_list.append({f"R_{r}" : 1})

    for d in dire:
        combos_list.append({f"D_{d}" : 1})

    for i in range(5):
        for j in range(i + 1 , 5):
            combos_list.append({f"Rpair_{radiant[i]}_{radiant[j]}" : 1})
            combos_list.append({f"Dpair_{dire[i]}_{dire[j]}" : 1})

    for r in radiant:
        for d in dire:
            combos_list.append({f"RvD_{r}_{d}" : 1})

    return combos_list


data = pd.read_csv("MLDotaDB.csv")
data.columns = ["id" , "match_id" , "radiant_win" , "hero_mask" , "team_mask"] # 0 - radiant , 1 - dire

x_dict = []
y = []

for _, row in data.iterrows():
    dire_mask = row['hero_mask'] & row['team_mask']
    radiant_mask = row['hero_mask'] ^ dire_mask
    vector = vector_from_bitmask(radiant_mask, dire_mask)
    match_dict = {}
    for d in vector:
        match_dict.update(d)
    x_dict.append(match_dict)
    y.append(int(row['radiant_win']))

X_spar = hasher.transform(x_dict)
Y = np.array(y)

X_train , X_test , Y_train , Y_test = train_test_split(X_spar , Y , test_size=0.2 , random_state=67)

md = xgb.XGBClassifier(n_estimators=500, max_depth=3, learning_rate=0.001, eval_metric='logloss')
md.fit(X_train, Y_train)

pred_y = md.predict(X_test)
proba_y = md.predict_proba(X_test)

print("accuracy: ", accuracy_score(Y_test , pred_y))
print("logloss: ", log_loss(Y_test , proba_y))

joblib.dump(md ,"dota_model.pkl")
print("ends")