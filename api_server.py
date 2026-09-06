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
import hmac
import os
from typing import Dict, Any, Optional
import time
from fastapi import FastAPI, HTTPException, Body, Security, Depends, status, Request
from fastapi.security import APIKeyHeader
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
from utils.bse_helper import resolve_indian_ticker
from utils.bse_bhavcopy import get_bse_eod_quote
from utils.auto_trader import evaluate_circuit_breakers
from utils.risk import compute_position_size
from utils.meta_labeling import evaluate_meta_labeling_filter

app = FastAPI(
    title="FinVision Headless Quantitative API",
    description="Institutional Market Regime, Risk Vetoes, and Webhook Router for Indian Equities.",
    version="3.0.0",
)

# Standards-compliant CORS configuration
allowed_origins_env = os.getenv("FINVISION_ALLOWED_ORIGINS", "")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Webhook Rate-Limiting Tracker (Finding D2)
_webhook_fail_tracker: dict[str, list[float]] = {}
WEBHOOK_MAX_ATTEMPTS = 10
WEBHOOK_WINDOW_SECONDS = 600
DEFAULT_ACCOUNT_CAPITAL = 500000.0


def _check_webhook_rate_limit(client_ip: str) -> bool:
    """Returns True if client IP is permitted to attempt webhook auth, False if locked out."""
    now = time.time()
    attempts = [t for t in _webhook_fail_tracker.get(client_ip, []) if now - t < WEBHOOK_WINDOW_SECONDS]
    _webhook_fail_tracker[client_ip] = attempts
    return len(attempts) < WEBHOOK_MAX_ATTEMPTS


def _record_webhook_failure(client_ip: str) -> None:
    """Records an authentication failure timestamp for rate-limiting."""
    now = time.time()
    attempts = [t for t in _webhook_fail_tracker.get(client_ip, []) if now - t < WEBHOOK_WINDOW_SECONDS]
    attempts.append(now)
    _webhook_fail_tracker[client_ip] = attempts


def get_api_key_secret() -> str:
    return os.getenv("FINVISION_API_KEY", "").strip()


def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)):
    """Verifies X-API-Key with fail-closed security (Finding D1)."""
    secret = get_api_key_secret()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured on this server (FINVISION_API_KEY unset). "
                   "Refusing to serve authenticated routes until an operator sets it.",
        )
    if not api_key or not hmac.compare_digest(api_key.strip(), secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing X-API-Key header."
        )
    return api_key


@app.on_event("startup")
def check_auth_configuration():
    secret = get_api_key_secret()
    if not secret:
        print("⚠️ CRITICAL SECURITY WARNING: FINVISION_API_KEY is unset. All authenticated /api/* routes will return HTTP 503 (Fail-Closed).")


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


@app.get("/api/regime", dependencies=[Depends(verify_api_key)])
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


@app.get("/api/setup/{ticker}", dependencies=[Depends(verify_api_key)])
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


@app.get("/api/gtt/{ticker}", dependencies=[Depends(verify_api_key)])
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


@app.get("/api/bse/resolve/{query}", dependencies=[Depends(verify_api_key)])
def resolve_bse(query: str, exchange: str = "NSE"):
    """Universally resolves any 6-digit BSE Scrip Code or alphabetical symbol."""
    res = resolve_indian_ticker(query, preferred_exchange=exchange)
    return {"status": "SUCCESS", "resolution": res}


@app.get("/api/bse/quote/{ticker_or_code}", dependencies=[Depends(verify_api_key)])
def get_bse_quote(ticker_or_code: str):
    """Retrieves official BSE EOD Bhavcopy quote and turnover stats from local database."""
    quote = get_bse_eod_quote(ticker_or_code)
    if not quote:
        resolved = resolve_indian_ticker(ticker_or_code)
        return {
            "status": "NOT_IN_LOCAL_BHAVCOPY",
            "resolution": resolved,
            "message": "Security resolved. Ingest latest Bhavcopy via /utils/bse_bhavcopy.py to populate EOD statistics."
        }
    return {"status": "SUCCESS", "quote": quote}


@app.post("/api/webhook/tradingview")
def receive_tradingview_alert(payload: TradingViewWebhookPayload, request: Request):
    """
    Receives alerts from TradingView Pine Script webhooks.
    Validates signal against FinVision's Risk Shields, Circuit Breakers, ML Ensemble & Regime Gatekeeper.
    Protected by mandatory passcode verification and brute-force IP rate-limiting (Findings C2 & D2).
    """
    client_ip = request.client.host if request.client else "unknown"
    if not _check_webhook_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed webhook passcode attempts. Access locked for 10 minutes."
        )

    configured_passcode = os.getenv("FINVISION_WEBHOOK_PASSCODE", "").strip() or get_api_key_secret()
    if not configured_passcode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook alert endpoint disabled: Set FINVISION_WEBHOOK_PASSCODE or FINVISION_API_KEY to accept alerts."
        )
    if not payload.passcode or not hmac.compare_digest(payload.passcode.strip(), configured_passcode):
        _record_webhook_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized webhook alert: Invalid or missing passcode."
        )

    # Finding C2: Route through Institutional Circuit Breakers
    cb = evaluate_circuit_breakers(capital=DEFAULT_ACCOUNT_CAPITAL, budget=DEFAULT_ACCOUNT_CAPITAL)
    if not cb.get("allow_new_entries", True):
        return {
            "status": "REJECTED_BY_RISK_SHIELD",
            "reason": cb.get("shield_status", "Circuit breaker active"),
        }

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

    # Finding C2: Route through Regime & Meta-Labeling Filter
    regime = detect_indian_market_regime()
    meta = evaluate_meta_labeling_filter(
        ticker=ticker,
        action=payload.action,
        entry_price=last_p,
        stop_loss=sl_p,
        target_price=target_p,
        conviction_pct=60.0,
        regime_code=regime.get("regime_code", "NORMAL_BALANCED"),
        vix_val=float(regime.get("vix_value", 14.5)),
    )
    if not meta.get("is_approved"):
        return {
            "status": "VETOED_BY_RISK_GATE",
            "reason": meta.get("verdict_explanation", "Vetoed by meta-labeling institutional risk gate."),
        }

    # Finding C2: Sizing from actual capital risk parameters (not hardcoded 10 shares)
    sizing = compute_position_size(
        total_capital=DEFAULT_ACCOUNT_CAPITAL,
        risk_pct=0.01 * float(meta.get("bet_sizing_factor", 1.0)),
        entry_price=last_p,
        stop_price=sl_p,
    )
    if sizing["shares"] <= 0:
        return {
            "status": "REJECTED_ZERO_SIZE",
            "reason": sizing.get("warning", "Risk sizing resulted in 0 shares."),
        }

    trade_id = log_paper_trade(
        ticker=ticker,
        trade_type=f"WEBHOOK_{payload.action.upper()}",
        entry_price=last_p,
        target_price=target_p,
        stop_loss_price=sl_p,
        shares=sizing["shares"],
        notes=f"TradingView Alert [{payload.strategy}] | Risk-Gated ({meta.get('status_badge', 'Approved')})",
        source="EXTERNAL_WEBHOOK",
        predicted_win_prob=float(meta.get("meta_win_probability_pct", 50.0)),
        regime_at_entry=regime.get("regime_code", "NORMAL"),
    )

    return {
        "status": "ACCEPTED_AND_LOGGED",
        "trade_id": trade_id,
        "ticker": ticker,
        "entry_price": last_p,
        "target_price": target_p,
        "stop_loss": sl_p,
        "shares": sizing["shares"],
        "ml_badge": ml_res.get("badge"),
        "meta_status": meta.get("status_badge"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinVision Headless REST & Webhook Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()

    print(f"🚀 Launching FinVision Headless Quant API on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
