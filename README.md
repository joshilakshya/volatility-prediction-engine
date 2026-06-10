# Volatility Prediction Engine

An AI-powered financial market volatility prediction engine that combines statistical volatility estimators, machine learning forecasting models, macroeconomic event studies, and risk analytics into a single deployable platform.

---

## Features

### Volatility Estimation

- Historical Volatility
- Rolling Volatility (20d, 60d, 120d)
- EWMA Volatility
- Parkinson Volatility
- Garman-Klass Volatility
- Realized Variance

### Forecasting Models

- GARCH
- EGARCH
- GJR-GARCH
- LSTM
- XGBoost
- Random Forest

### Event Study Module

- FOMC Events
- CPI Releases
- RBI Decisions
- Geopolitical Events

### Risk Metrics

- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio
- Value at Risk (VaR)
- Conditional VaR (CVaR)
- Maximum Drawdown

### VIX Integration

- Live VIX Data
- Realized vs Implied Volatility Comparison
- Divergence Analysis

---

## Tech Stack

### Backend

- Python 3.13
- FastAPI
- Pandas
- NumPy
- yFinance
- PyTorch
- XGBoost
- Scikit-Learn
- ARCH

### Frontend

- HTML
- CSS
- JavaScript

---

## System Architecture

![Architecture](docs/architecture.png)

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/volatility-prediction-engine.git
cd volatility-prediction-engine
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python main.py
```

or

```bash
uvicorn main:app --reload
```

---

## API Documentation

After launching:

```text
http://localhost:8000/docs
```

---

## Supported Assets

- S&P 500
- NASDAQ
- Dow Jones
- Nifty 50
- FTSE 100
- Nikkei 225
- DAX
- Hang Seng
- Gold
- Crude Oil
- Bitcoin

---

## Dashboard Modules

1. Overview
2. Volatility Analysis
3. VIX Analysis
4. Event Study
5. Risk Report
6. Forecasting

---

## Project Report

See:

```text
docs/project_report.pdf
```

---

## Authors

Priyanshi Faldu
Lakshya Joshi
Sammit Borekar

Symbiosis Institute of Technology
Department of Artificial Intelligence & Machine Learning
