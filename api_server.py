"""
finvision/api_server.py
=======================
Headless REST & Webhook API Server for FinVision v3.0 (FastAPI).
Inspired by Indian-Stock-Market-API and 0xramm.

Exposes FinVision's institutional quantitative intelligence to external systems:
  - n8n / Zapier automation workflows
  - TradingView Webhook alert filtering
  - Telegram / Discord bot morning dispatchers
  - Third-party algorithmic execution engines

Run with:
  python api_server.py --port 8000
"""

from __future__ import annotations
import argparse
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import yfinance as yf

from utils.regime import detect_indian_market_regime
from utils.macro import get_live_cross_asset_macro
from utils.forecasting import compute_quantitative_confluence_forecast
from utils.gtt import compute_gtt_order_parameters
from utils.tax_calculator import compute_indian_market_friction
from utils.market_store import log_paper_trade

app = FastAPI(
    title="FinVision Headless Quantitative API",
    description="Institutional Market Regime, ML Meta-Labeling, and Webhook Router for Indian Equities.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TradingViewWebhookPayload(BaseModel):
    ticker: str
    action: str  # BUY or SELL
    price: Optional[float] = None
    strategy: Optional[str] = "TradingView_Webhook"
    passcode: Optional[str] = None


@app.get("/")
def root():
    return {
        "status": "ONLINE",
        "service": "FinVision Headless Quant API",
        "version": "3.0.0",
        "endpoints": [
            "/api/regime",
            "/api/setup/{ticker}",
            "/api/gtt/{ticker}",
            "/api/webhook/tradingview",
        ]
    }


@app.get("/api/regime")
def get_regime():
    """Returns the live Indian Market Regime and Cross-Asset Macro Headwinds."""
    try:
        regime = detect_indian_market_regime()
        macro = get_live_cross_asset_macro()
        return {
            "status": "SUCCESS",
            "market_regime": regime,
            "cross_asset_macro": macro,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/setup/{ticker}")
def get_setup(ticker: str, forecast_days: int = 5):
    """Computes quantitative forecast, ML consensus, VaR, and risk levels for a stock."""
    try:
        clean_ticker = ticker.upper()
        if not clean_ticker.endswith(".NS") and not clean_ticker.endswith(".BO") and not clean_ticker.startswith("^"):
            clean_ticker += ".NS"

        df = yf.download(clean_ticker, period="1y", interval="1d", progress=False)
        if df.empty or len(df) < 30:
            raise HTTPException(status_code=404, detail=f"Insufficient market data for {clean_ticker}")

        fc = compute_quantitative_confluence_forecast(df=df, forecast_days=forecast_days)
        last_p = float(fc.get("last_price", df["Close"].iloc[-1]))
        entry_p = float(fc.get("tactical_buy_entry", last_p))
        t1_p = float(fc.get("take_profit", last_p * 1.03))
        sl_p = float(fc.get("stop_loss", last_p * 0.98))

        # Regulatory friction breakdown
        friction = compute_indian_market_friction(entry_p, t1_p, shares=100, is_intraday=True)

        # GTT Order math
        gtt_params = compute_gtt_order_parameters(
            ticker=clean_ticker,
            current_price=last_p,
            entry_price=entry_p,
            stop_loss=sl_p,
            target1=t1_p,
            shares=100,
        )

        return {
            "status": "SUCCESS",
            "ticker": clean_ticker,
            "last_price": last_p,
            "recommended_action": fc.get("recommended_action", "HOLD"),
            "conviction": fc.get("conviction", "MODERATE"),
            "entry_price": entry_p,
            "target1": t1_p,
            "target2": fc.get("target_2", 0.0),
            "stop_loss": sl_p,
            "risk_reward_ratio": fc.get("risk_reward_ratio", 2.0),
            "ml_ensemble": fc.get("ml_ensemble", {}),
            "tail_risk": fc.get("tail_risk", {}),
            "dynamic_factor_weights": fc.get("factor_weights", {}),
            "gtt_order_math": gtt_params,
            "friction_estimate_100sh": friction,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gtt/{ticker}")
def get_gtt(ticker: str):
    """Returns ready-to-copy GTT order parameters formatted for Zerodha Kite / Groww."""
    try:
        clean_ticker = ticker.upper()
        if not clean_ticker.endswith(".NS") and not clean_ticker.endswith(".BO"):
            clean_ticker += ".NS"

        df = yf.download(clean_ticker, period="6mo", interval="1d", progress=False)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Stock {clean_ticker} not found.")

        fc = compute_quantitative_confluence_forecast(df=df)
        last_p = float(fc.get("last_price", df["Close"].iloc[-1]))
        entry_p = float(fc.get("tactical_buy_entry", last_p))
        t1_p = float(fc.get("take_profit", last_p * 1.03))
        sl_p = float(fc.get("stop_loss", last_p * 0.98))

        gtt = compute_gtt_order_parameters(
            ticker=clean_ticker,
            current_price=last_p,
            entry_price=entry_p,
            stop_loss=sl_p,
            target1=t1_p,
            shares=50,
        )
        return {"status": "SUCCESS", "gtt_order": gtt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhook/tradingview")
def receive_tradingview_alert(payload: TradingViewWebhookPayload):
    """
    Receives alerts from TradingView Pine Script webhooks.
    Validates signal against FinVision's ML Ensemble & Regime Gatekeeper before simulated execution.
    """
    ticker = payload.ticker.upper()
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker += ".NS"

    # Rapid market data check
    df = yf.download(ticker, period="60d", interval="1d", progress=False)
    if df.empty:
        return {"status": "REJECTED", "reason": f"Unknown ticker: {ticker}"}

    fc = compute_quantitative_confluence_forecast(df=df)
    ml_res = fc.get("ml_ensemble", {})

    # Check for ML Divergence Veto
    if ml_res.get("verdict") == "DIVERGENCE_VETO":
        return {
            "status": "VETOED_BY_AI",
            "message": "Signal rejected: Machine Learning trees detected strong momentum divergence against the alert direction.",
            "ml_consensus": ml_res.get("badge"),
        }

    last_p = payload.price or float(fc.get("last_price", df["Close"].iloc[-1]))
    target_p = float(fc.get("take_profit", last_p * 1.025))
    sl_p = float(fc.get("stop_loss", last_p * 0.985))

    trade_id = log_paper_trade(
        ticker=ticker,
        trade_type=f"WEBHOOK_{payload.action.upper()}",
        entry_price=last_p,
        target_price=target_p,
        stop_loss_price=sl_p,
        shares=10,
        notes=f"TradingView Alert [{payload.strategy}]: ML Confirmed ({ml_res.get('badge', 'Active')})",
    )

    return {
        "status": "ACCEPTED_AND_LOGGED",
        "trade_id": trade_id,
        "ticker": ticker,
        "entry_price": last_p,
        "target_price": target_p,
        "stop_loss": sl_p,
        "ml_badge": ml_res.get("badge"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinVision Headless REST & Webhook Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()

    print(f"🚀 Launching FinVision Headless Quant API on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
