import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import accuracy_score, log_loss
from sklearn.isotonic import IsotonicRegression
import numpy as np
import joblib
import scipy.sparse as sp


X_train = sp.load_npz("X_train.npz")
X_calib  = sp.load_npz("X_calib.npz")
X_test   = sp.load_npz("X_test.npz")
y_train  = np.load("y_train.npy")
y_calib  = np.load("y_calib.npy")
y_test   = np.load("y_test.npy")

print(f"features: {X_train.shape[1]}, train: {X_train.shape[0]}")

class EnsembleModel:
    def __init__(self, xgb_model, lgb_model, xgb_iso, lgb_iso):
        self.xgb_model = xgb_model
        self.lgb_model = lgb_model
        self.xgb_iso   = xgb_iso
        self.lgb_iso   = lgb_iso

    def predict_proba(self, X):
        xgb_raw = self.xgb_model.predict_proba(X)[:, 1]
        lgb_raw = self.lgb_model.predict_proba(X)[:, 1]
        xgb_cal = self.xgb_iso.predict(xgb_raw)
        lgb_cal = self.lgb_iso.predict(lgb_raw)
        return (xgb_cal + lgb_cal) / 2.0

    def predict(self, X):
        return (self.predict_proba(X) >= 0.5).astype(int)

print("training XGBoost...")
xgb_model = xgb.XGBClassifier(
    n_estimators=9000,
    max_depth=5,
    learning_rate=0.04,
    subsample=0.85,
    colsample_bytree=0.6,
    colsample_bylevel=0.7,
    reg_alpha=0.7,
    reg_lambda=2.5,
    min_child_weight=7,
    gamma=0.05,
    eval_metric='logloss',
    random_state=67,
    tree_method='hist',
    device='cuda'
)
xgb_model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=200
)

print("training LightGBM...")
lgb_model = lgb.LGBMClassifier(
    n_estimators=1000,
    max_depth=-1,
    num_leaves=63,
    learning_rate=0.07,
    subsample=0.85,
    colsample_bytree=0.6,
    reg_alpha=0.7,
    reg_lambda=2.5,
    min_child_samples=20,
    device='gpu',
    gpu_use_dp=False,
    gpu_platform_id=0,
    gpu_device_id=0,
    random_state=67,
    verbose=-1
)

lgb_model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    callbacks=[lgb.log_evaluation(100)]
)

print("calibrating...")
xgb_raw = xgb_model.predict_proba(X_calib)[:, 1]
lgb_raw = lgb_model.predict_proba(X_calib)[:, 1]

xgb_iso = IsotonicRegression(out_of_bounds='clip')
xgb_iso.fit(xgb_raw, y_calib)

lgb_iso = IsotonicRegression(out_of_bounds='clip')
lgb_iso.fit(lgb_raw, y_calib)

model = EnsembleModel(xgb_model, lgb_model, xgb_iso, lgb_iso)

xgb_raw_test = xgb_model.predict_proba(X_test)[:, 1]
lgb_raw_test = lgb_model.predict_proba(X_test)[:, 1]
xgb_cal_test = xgb_iso.predict(xgb_raw_test)
lgb_cal_test = lgb_iso.predict(lgb_raw_test)
ens_test = (xgb_cal_test + lgb_cal_test) / 2.0
xgb_pred = (xgb_cal_test >= 0.5).astype(int)
lgb_pred = (lgb_cal_test >= 0.5).astype(int)
ens_pred = (ens_test >= 0.5).astype(int)

print(f"XGBoost  | acc: {accuracy_score(y_test, xgb_pred):.4f} | logloss: {log_loss(y_test, xgb_cal_test):.4f}")
print(f"LightGBM | acc: {accuracy_score(y_test, lgb_pred):.4f} | logloss: {log_loss(y_test, lgb_cal_test):.4f}")
print(f"Ensemble | acc: {accuracy_score(y_test, ens_pred):.4f} | logloss: {log_loss(y_test, ens_test):.4f}")

joblib.dump(model, "model.pkl")
print("saved.")