import pandas as pd
import numpy as np
from config import settings
from data.preprocessor import regime_label

def current_snapshot(df: pd.DataFrame) -> dict:
    row = df.dropna(subset=["Vol_20d"]).iloc[-1]
    vol20 = float(row.get("Vol_20d", np.nan))
    return {
        "date": str(df.index[-1].date()),
        "close": float(row["Close"]),
        "return_1d": float(row.get("Return", np.nan)),
        "vol_20d": round(vol20, 4),
        "vol_60d": round(float(row.get("Vol_60d", np.nan)), 4),
        "vol_120d": round(float(row.get("Vol_120d", np.nan)), 4),
        "ewma_vol": round(float(row.get("EWMA_Vol", np.nan)), 4),
        "parkinson_vol": round(float(row.get("Parkinson_Vol", np.nan)), 4),
        "garman_klass_vol": round(float(row.get("GarmanKlass_Vol", np.nan)), 4),
        "realvol_21d": round(float(row.get("RealVol_21d", np.nan)), 4),
        "regime": regime_label(vol20),
        "drawdown": round(float(row.get("Drawdown", np.nan)), 4),
    }

def rolling_comparison(df: pd.DataFrame) -> list:
    cols = ["Close","LogReturn","Vol_20d","Vol_60d","Vol_120d","EWMA_Vol","Parkinson_Vol","GarmanKlass_Vol"]
    sub = df[[c for c in cols if c in df.columns]].dropna(how="all")
    records = []
    for idx, row in sub.iterrows():
        r = {"date": str(idx.date())}
        for c in cols:
            if c in row.index and not pd.isna(row[c]):
                r[c] = round(float(row[c]), 6)
        records.append(r)
    return records

def estimator_compare_table(df: pd.DataFrame) -> dict:
    cols = {
        "Historical": "Vol_20d",
        "Rolling 60d": "Vol_60d",
        "Rolling 120d": "Vol_120d",
        "EWMA": "EWMA_Vol",
        "Parkinson": "Parkinson_Vol",
        "Garman-Klass": "GarmanKlass_Vol",
        "Realised (21d)": "RealVol_21d",
    }
    result = {}
    for name, col in cols.items():
        if col in df.columns:
            s = df[col].dropna()
            result[name] = {
                "current": round(float(s.iloc[-1]), 4) if len(s) else None,
                "mean": round(float(s.mean()), 4),
                "min": round(float(s.min()), 4),
                "max": round(float(s.max()), 4),
                "std": round(float(s.std()), 4),
            }
    return result
