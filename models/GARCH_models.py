import pandas as pd
import numpy as np
from arch import arch_model
from config import settings
import logging

logger = logging.getLogger("volatility_engine")

def _scale(returns: pd.Series):
    return returns * 100

def fit_best_garch(returns: pd.Series) -> dict:
    scaled = _scale(returns.dropna())
    best_bic = np.inf
    best_res = None
    best_spec = None

    specs = [
        ("GARCH", "normal", 1, 1),
        ("EGARCH", "normal", 1, 1),
        ("GARCH", "skewt", 1, 1),
        ("GJR-GARCH", "normal", 1, 1),
    ]

    for vol_model, dist, p, q in specs:
        try:
            am = arch_model(scaled, vol=vol_model, p=p, q=q, dist=dist)
            res = am.fit(disp="off", show_warning=False)
            if res.bic < best_bic:
                best_bic = res.bic
                best_res = res
                best_spec = {"model": vol_model, "dist": dist, "p": p, "q": q}
        except Exception as e:
            logger.debug(f"GARCH spec {vol_model}({p},{q}) failed: {e}")
            continue

    if best_res is None:
        raise ValueError("All GARCH specs failed")

    return {"result": best_res, "spec": best_spec, "bic": best_bic}

def forecast_volatility(returns: pd.Series, horizon: int = 10) -> dict:
    try:
        fitted = fit_best_garch(returns)
        res = fitted["result"]
        fc = res.forecast(horizon=horizon, reindex=False)
        var_array = fc.variance.values[-1]
        vol_array = np.sqrt(var_array) / 100 * np.sqrt(settings.trading_days)
        return {
            "model": fitted["spec"]["model"],
            "distribution": fitted["spec"]["dist"],
            "bic": round(fitted["bic"], 4),
            "horizon_days": horizon,
            "forecast_vol": [round(float(v), 4) for v in vol_array],
            "forecast_mean_vol": round(float(vol_array.mean()), 4),
            "params": {k: round(float(v), 6) for k, v in res.params.items()},
        }
    except Exception as e:
        logger.error(f"GARCH forecast error: {e}")
        raise
