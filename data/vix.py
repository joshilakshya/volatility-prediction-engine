import yfinance as yf
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("volatility_engine")

def fetch_vix(period: str = "5y") -> pd.DataFrame:
    try:
        vix = yf.Ticker("^VIX").history(period=period, auto_adjust=True)
        vix.index = pd.to_datetime(vix.index).tz_localize(None)
        vix = vix[["Close"]].rename(columns={"Close": "VIX"})
        vix["VIX_decimal"] = vix["VIX"] / 100.0
        vix.dropna(inplace=True)
        return vix
    except Exception as e:
        logger.error(f"VIX fetch failed: {e}")
        return pd.DataFrame()

def merge_vix(df: pd.DataFrame, period: str = "5y") -> pd.DataFrame:
    vix = fetch_vix(period)
    if vix.empty:
        return df
    merged = df.join(vix, how="left")
    merged["VIX_decimal"] = merged["VIX_decimal"].ffill()
    merged["VIX"] = merged["VIX"].ffill()
    return merged

def vix_divergence(df: pd.DataFrame) -> pd.DataFrame:
    if "VIX_decimal" not in df.columns or "Vol_20d" not in df.columns:
        return df
    df = df.copy()
    df["VIX_Divergence"] = df["VIX_decimal"] - df["Vol_20d"]
    def sig(d):
        if pd.isna(d): return "unknown"
        if d > 0.02: return "fear_premium"
        if d < -0.02: return "complacency"
        return "aligned"
    df["VIX_Signal"] = df["VIX_Divergence"].apply(sig)
    return df

def current_vix_snapshot() -> dict:
    try:
        vix = fetch_vix(period="5d")
        if vix.empty:
            return {"vix": None, "regime": "unavailable"}
        latest = float(vix["VIX"].iloc[-1])
        if latest < 15: regime = "Low Fear"
        elif latest < 25: regime = "Moderate"
        elif latest < 35: regime = "High Fear"
        else: regime = "Extreme Fear"
        return {"vix": round(latest, 2), "regime": regime}
    except:
        return {"vix": None, "regime": "unavailable"}
