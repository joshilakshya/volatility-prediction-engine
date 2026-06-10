import numpy as np
import pandas as pd
from config import settings
import logging

logger = logging.getLogger("volatility_engine")

def train_lstm(df: pd.DataFrame, horizon: int = 5) -> dict:
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch not installed. Run: pip install torch --index-url https://download.pytorch.org/whl/cpu")

    target_col = "Vol_20d"
    series = df[target_col].dropna().values.astype(np.float32)
    if len(series) < settings.lstm_lookback + 20:
        raise ValueError(f"Need at least {settings.lstm_lookback + 20} rows for LSTM")

    # Normalise
    mu, sigma = series.mean(), series.std()
    normed = (series - mu) / sigma

    lb = settings.lstm_lookback
    X, y = [], []
    for i in range(len(normed) - lb - horizon):
        X.append(normed[i:i+lb])
        y.append(normed[i+lb+horizon-1])

    X = torch.tensor(np.array(X)).unsqueeze(-1)
    y = torch.tensor(np.array(y))

    split = int(0.85 * len(X))
    X_tr, X_va = X[:split], X[split:]
    y_tr, y_va = y[:split], y[split:]

    class LSTMModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(1, settings.lstm_hidden, num_layers=2,
                                batch_first=True, dropout=0.2)
            self.fc = nn.Linear(settings.lstm_hidden, 1)
        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :]).squeeze(-1)

    model = LSTMModel()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=5, factor=0.5)
    loss_fn = nn.MSELoss()

    best_val, patience, best_ep = np.inf, 0, 0
    train_losses, val_losses = [], []

    for ep in range(settings.lstm_epochs):
        model.train()
        opt.zero_grad()
        pred = model(X_tr)
        loss = loss_fn(pred, y_tr)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        model.eval()
        with torch.no_grad():
            vl = loss_fn(model(X_va), y_va).item()
        sched.step(vl)
        train_losses.append(loss.item())
        val_losses.append(vl)

        if vl < best_val:
            best_val = vl
            best_ep = ep
            patience = 0
        else:
            patience += 1
            if patience >= 10:
                break

    # Forecast
    model.eval()
    seed = torch.tensor(normed[-lb:]).unsqueeze(0).unsqueeze(-1)
    forecasts = []
    with torch.no_grad():
        inp = seed.clone()
        for _ in range(horizon):
            out = model(inp).item()
            forecasts.append(float(out * sigma + mu))
            new_step = torch.tensor([[[out]]])
            inp = torch.cat([inp[:, 1:, :], new_step], dim=1)

    return {
        "model": "LSTM",
        "epochs_trained": best_ep + 1,
        "train_rmse": round(float(np.sqrt(np.mean(np.array(train_losses)))), 6),
        "val_rmse": round(float(np.sqrt(best_val)), 6),
        "forecast_vol": [round(f, 4) for f in forecasts],
        "forecast_mean_vol": round(float(np.mean(forecasts)), 4),
        "horizon_days": horizon,
    }
