from fastapi import APIRouter, Query
from data.loader import get_data
from data.preprocessor import build_features
from models.statistical import current_snapshot, rolling_comparison, estimator_compare_table
from utils.metrics import compute_risk_metrics

router = APIRouter(prefix="/volatility", tags=["Volatility"])

@router.get("/current")
def get_current(ticker: str = Query("^GSPC"), period: str = Query("5y")):
    df = build_features(get_data(ticker, period))
    return current_snapshot(df)

@router.get("/compare")
def get_compare(ticker: str = Query("^GSPC"), period: str = Query("5y")):
    df = build_features(get_data(ticker, period))
    return estimator_compare_table(df)

@router.get("/rolling")
def get_rolling(ticker: str = Query("^GSPC"), period: str = Query("5y")):
    df = build_features(get_data(ticker, period))
    return rolling_comparison(df)

@router.get("/risk-metrics")
def get_risk(ticker: str = Query("^GSPC"), period: str = Query("5y")):
    df = build_features(get_data(ticker, period))
    return compute_risk_metrics(df)

@router.get("/dataset")
def get_dataset(ticker: str = Query("^GSPC"), period: str = Query("5y")):
    df = build_features(get_data(ticker, period))
    df2 = df.reset_index()
    df2["Date"] = df2["Date"].astype(str)
    # Guarantee consistent key names regardless of pandas version
    rename = {c: c for c in df2.columns}
    for col in df2.columns:
        if col.lower() in ("logreturn", "log_return"):
            rename[col] = "LogReturn"
        if col.lower() in ("return", "ret"):
            rename[col] = "Return"
    df2.rename(columns=rename, inplace=True)
    return df2.where(df2.notna(), None).to_dict(orient="records")
