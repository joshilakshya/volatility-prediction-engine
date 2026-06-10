import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from xgboost import XGBRegressor
from config import settings
import logging

logger = logging.getLogger("volatility_engine")

FEATURE_COLS = [
    "LogReturn","Vol_20d","Vol_60d","EWMA_Vol",
    "Parkinson_Vol","GarmanKlass_Vol","MA_20","MA_50","Drawdown"
]

def _prepare(df: pd.DataFrame, target_col: str = "Vol_20d", horizon: int = 5):
    feats = [c for c in FEATURE_COLS if c in df.columns]
    sub = df[feats + [target_col]].dropna()
    X = sub[feats].values[:-horizon]
    y = sub[target_col].shift(-horizon).dropna().values
    n = min(len(X), len(y))
    return X[:n], y[:n], feats

def train_xgboost(df: pd.DataFrame, horizon: int = 5) -> dict:
    X, y, feats = _prepare(df, horizon=horizon)
    if len(X) < 60:
        raise ValueError("Insufficient data for XGBoost")
    tscv = TimeSeriesSplit(n_splits=5)
    cv_rmse = []
    for tr, va in tscv.split(X):
        m = XGBRegressor(n_estimators=settings.xgb_trees, learning_rate=0.05,
                         max_depth=4, subsample=0.8, random_state=42, verbosity=0)
        m.fit(X[tr], y[tr])
        pred = m.predict(X[va])
        cv_rmse.append(np.sqrt(mean_squared_error(y[va], pred)))

    final = XGBRegressor(n_estimators=settings.xgb_trees, learning_rate=0.05,
                         max_depth=4, subsample=0.8, random_state=42, verbosity=0)
    final.fit(X, y)
    pred_all = final.predict(X)
    fi = dict(zip(feats, final.feature_importances_.tolist()))

    last_X = X[-1].reshape(1, -1)
    forecast = [round(float(final.predict(last_X)[0]), 4)] * horizon

    return {
        "model": "XGBoost",
        "rmse": round(float(np.mean(cv_rmse)), 6),
        "mae": round(float(mean_absolute_error(y, pred_all)), 6),
        "r2": round(float(r2_score(y, pred_all)), 4),
        "cv_rmse_mean": round(float(np.mean(cv_rmse)), 6),
        "feature_importance": fi,
        "forecast_vol": forecast,
        "forecast_mean_vol": round(float(np.mean(forecast)), 4),
        "horizon_days": horizon,
    }

def train_random_forest(df: pd.DataFrame, horizon: int = 5) -> dict:
    X, y, feats = _prepare(df, horizon=horizon)
    if len(X) < 60:
        raise ValueError("Insufficient data for Random Forest")
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)
    tscv = TimeSeriesSplit(n_splits=5)
    cv_rmse = []
    for tr, va in tscv.split(X_sc):
        m = RandomForestRegressor(n_estimators=settings.rf_trees, random_state=42, n_jobs=-1)
        m.fit(X_sc[tr], y[tr])
        pred = m.predict(X_sc[va])
        cv_rmse.append(np.sqrt(mean_squared_error(y[va], pred)))

    final = RandomForestRegressor(n_estimators=settings.rf_trees, random_state=42, n_jobs=-1)
    final.fit(X_sc, y)
    pred_all = final.predict(X_sc)
    fi = dict(zip(feats, final.feature_importances_.tolist()))

    last_X = scaler.transform(X[-1].reshape(1, -1))
    forecast = [round(float(final.predict(last_X)[0]), 4)] * horizon

    return {
        "model": "RandomForest",
        "rmse": round(float(np.mean(cv_rmse)), 6),
        "mae": round(float(mean_absolute_error(y, pred_all)), 6),
        "r2": round(float(r2_score(y, pred_all)), 4),
        "cv_rmse_mean": round(float(np.mean(cv_rmse)), 6),
        "feature_importance": fi,
        "forecast_vol": forecast,
        "forecast_mean_vol": round(float(np.mean(forecast)), 4),
        "horizon_days": horizon,
    }
