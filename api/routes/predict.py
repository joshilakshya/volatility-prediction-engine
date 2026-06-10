from fastapi import APIRouter, Query, HTTPException
from data.loader import get_data
from data.preprocessor import build_features
from models.garch_model import forecast_volatility
from models.ml_models import train_xgboost, train_random_forest
from models.lstm_model import train_lstm

router = APIRouter(prefix="/predict", tags=["Predict"])

@router.get("/garch")
def garch_forecast(ticker: str = Query("^GSPC"), period: str = Query("5y"), horizon: int = Query(10)):
    try:
        df = build_features(get_data(ticker, period))
        return forecast_volatility(df["LogReturn"].dropna(), horizon)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/xgboost")
def xgb_forecast(ticker: str = Query("^GSPC"), period: str = Query("5y"), horizon: int = Query(5)):
    try:
        df = build_features(get_data(ticker, period))
        return train_xgboost(df, horizon)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/random-forest")
def rf_forecast(ticker: str = Query("^GSPC"), period: str = Query("5y"), horizon: int = Query(5)):
    try:
        df = build_features(get_data(ticker, period))
        return train_random_forest(df, horizon)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/lstm")
def lstm_forecast(ticker: str = Query("^GSPC"), period: str = Query("5y"), horizon: int = Query(5)):
    try:
        df = build_features(get_data(ticker, period))
        return train_lstm(df, horizon)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
