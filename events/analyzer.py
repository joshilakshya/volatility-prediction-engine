import pandas as pd
import numpy as np
from events.calendar import MACRO_EVENTS

def run_event_study(df: pd.DataFrame, window: int = 10, events: list = None) -> list:
    events = events or MACRO_EVENTS
    results = []
    df = df.copy()
    df.index = pd.to_datetime(df.index)

    for ev in events:
        try:
            ev_date = pd.to_datetime(ev["date"])
            mask = df.index <= ev_date
            if mask.sum() == 0:
                continue
            pos = df.index.get_indexer([ev_date], method="ffill")[0]
            if pos < window or pos + window >= len(df):
                continue

            pre = df.iloc[pos - window:pos]
            post = df.iloc[pos:pos + window]

            col = "LogReturn"
            if col not in df.columns:
                continue

            pre_vol = float(pre[col].std() * np.sqrt(252))
            post_vol = float(post[col].std() * np.sqrt(252))
            shock_ratio = post_vol / pre_vol if pre_vol > 0 else np.nan

            post_ret = float(post[col].sum())
            cum_ret = float((1 + post[col]).prod() - 1)
            dd = float(((post["Close"] / post["Close"].cummax()) - 1).min())

            if np.isnan(shock_ratio):
                impact = "unknown"
            elif shock_ratio > 1.25:
                impact = "Amplifying"
            elif shock_ratio < 0.80:
                impact = "Dampening"
            else:
                impact = "Neutral"

            results.append({
                "date": ev["date"],
                "name": ev["name"],
                "category": ev["category"],
                "pre_vol": round(pre_vol, 4),
                "post_vol": round(post_vol, 4),
                "shock_ratio": round(shock_ratio, 4),
                "avg_post_return": round(post_ret / window, 6),
                "cumulative_return": round(cum_ret, 4),
                "max_drawdown": round(dd, 4),
                "impact": impact,
            })
        except Exception:
            continue

    results.sort(key=lambda x: x.get("shock_ratio", 0), reverse=True)
    return results

def summarise_study(results: list) -> dict:
    if not results:
        return {}
    cats = {}
    for r in results:
        c = r["category"]
        cats.setdefault(c, []).append(r["shock_ratio"])

    amplifying = [r for r in results if r["impact"] == "Amplifying"]
    dampening  = [r for r in results if r["impact"] == "Dampening"]
    neutral    = [r for r in results if r["impact"] == "Neutral"]

    return {
        "total_events": len(results),
        "amplifying": len(amplifying),
        "neutral": len(neutral),
        "dampening": len(dampening),
        "avg_shock_ratio": round(float(np.mean([r["shock_ratio"] for r in results])), 4),
        "most_amplifying": max(results, key=lambda x: x["shock_ratio"])["name"] if results else None,
        "by_category": {c: round(float(np.mean(v)), 4) for c, v in cats.items()},
    }
