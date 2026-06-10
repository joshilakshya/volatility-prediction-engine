from fastapi import APIRouter, Query, HTTPException
from data.loader import get_data
from data.preprocessor import build_features
from data.vix import fetch_vix, merge_vix, vix_divergence, current_vix_snapshot
from models.garch_model import forecast_volatility
import numpy as np

router = APIRouter(prefix="/vix", tags=["VIX"])

@router.get("/snapshot")
def vix_snapshot():
    return current_vix_snapshot()

@router.get("/history")
def vix_history(period: str = Query("5y")):
    vix = fetch_vix(period)
    if vix.empty:
        raise HTTPException(status_code=503, detail="VIX data unavailable")
    vix = vix.reset_index()
    vix["Date"] = vix["Date"].astype(str)
    return vix[["Date","VIX","VIX_decimal"]].to_dict(orient="records")

@router.get("/compare")
def vix_vs_realised(ticker: str = Query("^GSPC"), period: str = Query("5y")):
    df = build_features(get_data(ticker, period))
    # Always include rolling cols; try to merge VIX on top
    try:
        df = merge_vix(df, period)
        df = vix_divergence(df)
    except Exception:
        pass
    cols = ["Vol_20d","Vol_60d","EWMA_Vol","VIX_decimal","VIX_Divergence","VIX_Signal"]
    available = [c for c in cols if c in df.columns]
    # Must have at least Vol_20d
    sub = df[available].dropna(subset=["Vol_20d"])
    sub = sub.reset_index()
    sub["Date"] = sub["Date"].astype(str)
    return sub.where(sub.notna(), None).to_dict(orient="records")

@router.get("/forecast-compare")
def vix_vs_garch(ticker: str = Query("^GSPC"), period: str = Query("5y"), horizon: int = Query(10)):
    try:
        df = build_features(get_data(ticker, period))
        df = merge_vix(df, period)
        fc = forecast_volatility(df["LogReturn"].dropna(), horizon)
        vix_snap = current_vix_snapshot()
        vix_dec = (vix_snap["vix"] or 0) / 100
        model_mean = fc["forecast_mean_vol"]
        diff = model_mean - vix_dec
        if diff > 0.02:
            signal = "model_more_bearish"
        elif diff < -0.02:
            signal = "model_more_bullish"
        else:
            signal = "aligned"
        return {
            "vix_current": vix_snap["vix"],
            "vix_implied_vol": round(vix_dec, 4),
            "vix_regime": vix_snap["regime"],
            "garch_model": fc["model"],
            "garch_forecast_mean": model_mean,
            "garch_forecast_vol": fc["forecast_vol"],
            "divergence": round(diff, 4),
            "signal": signal,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
