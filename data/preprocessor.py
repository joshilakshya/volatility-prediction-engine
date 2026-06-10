import pandas as pd
import numpy as np
from config import settings

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.sort_index(inplace=True)

    # Returns
    df["Return"] = df["Close"].pct_change()
    df["LogReturn"] = np.log(df["Close"] / df["Close"].shift(1))

    ann = np.sqrt(settings.trading_days)

    # Rolling volatilities
    for w in settings.rolling_windows:
        df[f"Vol_{w}d"] = df["LogReturn"].rolling(w).std() * ann

    # EWMA volatility
    lam = settings.ewma_lambda
    ewma_var = df["LogReturn"].ewm(com=(1-lam)/lam, adjust=False).var()
    df["EWMA_Vol"] = np.sqrt(ewma_var) * ann

    # Parkinson estimator
    df["Parkinson_Vol"] = (
        np.sqrt(1 / (4 * np.log(2)) * (np.log(df["High"] / df["Low"]) ** 2))
        * ann
    )

    # Garman-Klass estimator
    df["GarmanKlass_Vol"] = np.sqrt(
        0.5 * (np.log(df["High"] / df["Low"]) ** 2)
        - (2 * np.log(2) - 1) * (np.log(df["Close"] / df["Open"]) ** 2)
    ) * ann

    # Realised variance (21-day)
    df["RealVol_21d"] = df["LogReturn"].rolling(21).apply(
        lambda x: np.sqrt(np.sum(x**2)) * ann, raw=True
    )

    # Moving averages
    for w in [20, 50, 200]:
        df[f"MA_{w}"] = df["Close"].rolling(w).mean()

    # Drawdown
    peak = df["Close"].expanding().max()
    df["Drawdown"] = (df["Close"] - peak) / peak

    df.dropna(how="all", subset=["Return","LogReturn"], inplace=True)
    return df

def regime_label(vol: float) -> str:
    if vol is None or np.isnan(vol):
        return "unknown"
    if vol < 0.10:
        return "Low"
    elif vol < 0.20:
        return "Medium"
    else:
        return "High"
