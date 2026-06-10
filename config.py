from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Volatility Prediction Engine"
    version: str = "3.0.0"
    default_ticker: str = "^GSPC"
    default_period: str = "5y"
    default_interval: str = "1d"
    ewma_lambda: float = 0.94
    rolling_windows: list = [20, 60, 120]
    min_rows_for_models: int = 120
    lstm_lookback: int = 60
    lstm_epochs: int = 50
    lstm_hidden: int = 64
    garch_specs: list = [(1,1),(1,2),(2,1)]
    rf_trees: int = 200
    xgb_trees: int = 300
    risk_free_rate: float = 0.05
    trading_days: int = 252
    var_confidence: list = [0.95, 0.99]

settings = Settings()
