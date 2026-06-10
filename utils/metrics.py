import numpy as np
import pandas as pd
from config import settings

def compute_risk_metrics(df: pd.DataFrame) -> dict:
    ret = df["LogReturn"].dropna()
    close = df["Close"].dropna()

    ann_ret = float(ret.mean() * settings.trading_days)
    ann_vol = float(ret.std() * np.sqrt(settings.trading_days))
    rf = settings.risk_free_rate

    sharpe = (ann_ret - rf) / ann_vol if ann_vol > 0 else np.nan

    neg = ret[ret < 0]
    sortino_denom = float(neg.std() * np.sqrt(settings.trading_days))
    sortino = (ann_ret - rf) / sortino_denom if sortino_denom > 0 else np.nan

    peak = close.cummax()
    dd = ((close - peak) / peak)
    max_dd = float(dd.min())
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else np.nan

    var_95 = float(np.percentile(ret, 5))
    var_99 = float(np.percentile(ret, 1))
    cvar_95 = float(ret[ret <= var_95].mean())
    cvar_99 = float(ret[ret <= var_99].mean())

    skew = float(ret.skew())
    kurt = float(ret.kurtosis())

    return {
        "annualised_return": round(ann_ret, 4),
        "annualised_volatility": round(ann_vol, 4),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "calmar_ratio": round(calmar, 4),
        "max_drawdown": round(max_dd, 4),
        "var_95": round(var_95, 4),
        "var_99": round(var_99, 4),
        "cvar_95": round(cvar_95, 4),
        "cvar_99": round(cvar_99, 4),
        "skewness": round(skew, 4),
        "kurtosis": round(kurt, 4),
        "total_trading_days": int(len(ret)),
    }
