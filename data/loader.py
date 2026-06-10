import yfinance as yf
import pandas as pd
import io
from config import settings
import logging

logger = logging.getLogger("volatility_engine")

def fetch_from_yfinance(ticker: str = None, period: str = None, interval: str = None) -> pd.DataFrame:
    ticker = ticker or settings.default_ticker
    period = period or settings.default_period
    interval = interval or settings.default_interval
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            raise ValueError(f"No data returned for {ticker}")
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df[["Open","High","Low","Close","Volume"]].copy()
        df.dropna(inplace=True)
        logger.info(f"Fetched {len(df)} rows from yfinance for {ticker}")
        return df
    except Exception as e:
        logger.error(f"yfinance fetch failed: {e}")
        raise

def load_from_csv(content: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(content))
        df.columns = [c.strip() for c in df.columns]
        date_col = next((c for c in df.columns if "date" in c.lower()), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
        col_map = {}
        for col in df.columns:
            cl = col.lower()
            if "open" in cl: col_map[col] = "Open"
            elif "high" in cl: col_map[col] = "High"
            elif "low" in cl: col_map[col] = "Low"
            elif "close" in cl and "adj" not in cl: col_map[col] = "Close"
            elif "volume" in cl or "vol" in cl: col_map[col] = "Volume"
        df.rename(columns=col_map, inplace=True)
        for c in ["Open","High","Low","Close"]:
            if c not in df.columns:
                df[c] = df.get("Close", 100.0)
        if "Volume" not in df.columns:
            df["Volume"] = 0
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        return df
    except Exception as e:
        raise ValueError(f"CSV parse error: {e}")

def get_data(ticker: str = None, period: str = None, csv_content: bytes = None) -> pd.DataFrame:
    if csv_content:
        df = load_from_csv(csv_content)
        if len(df) < settings.min_rows_for_models:
            try:
                yf_df = fetch_from_yfinance(ticker, period)
                combined = pd.concat([yf_df, df])
                combined = combined[~combined.index.duplicated(keep="last")]
                combined.sort_index(inplace=True)
                logger.info(f"Extended CSV ({len(df)} rows) with yfinance → {len(combined)} rows")
                return combined
            except:
                return df
        return df
    return fetch_from_yfinance(ticker, period)
