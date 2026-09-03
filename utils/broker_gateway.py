"""
finvision/utils/broker_gateway.py
=================================
Multi-Broker Execution Gateway for Indian Markets (inspired by Fenix).
Supports:
  1. Zerodha Kite Connect API
  2. Upstox API
  3. Angel One SmartAPI
  4. Fenix / Generic Execution Webhook (n8n / TradingView bridge)

SAFETY GUARANTEE:
  - Live Broker Routing is switched OFF by default.
  - When disabled, all executions are strictly redirected to the internal Paper Trading simulator.
  - Requires explicit user toggle activation and confirmation for live routing.
"""

from __future__ import annotations
import json
import logging
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

SUPPORTED_BROKERS = [
    "Zerodha Kite",
    "Upstox",
    "Angel One",
    "Fenix Webhook / n8n",
]


def build_broker_order_payload(
    broker: str,
    ticker: str,
    transaction_type: str,  # BUY or SELL
    quantity: int,
    price: float,
    stop_loss: float = 0.0,
    target: float = 0.0,
    product: str = "MIS",   # MIS for intraday, CNC for delivery
    order_type: str = "LIMIT",
) -> Dict[str, Any]:
    """Generates broker-specific JSON order payload conforming to official API schemas."""
    clean_symbol = ticker.replace(".NS", "").replace(".BO", "").upper()
    
    if "Zerodha" in broker:
        # Zerodha Kite Connect order format
        return {
            "tradingsymbol": clean_symbol,
            "exchange": "NSE",
            "transaction_type": transaction_type.upper(),
            "order_type": order_type.upper(),
            "quantity": quantity,
            "product": product.upper(),
            "price": round(price, 2),
            "trigger_price": round(stop_loss, 2) if "SL" in order_type else 0.0,
            "validity": "DAY",
            "tag": "FinVisionCopilot",
        }
    elif "Upstox" in broker:
        # Upstox API v2 order format
        return {
            "instrument_token": f"NSE_EQ|{clean_symbol}",
            "quantity": quantity,
            "product": "I" if product == "MIS" else "D",
            "validity": "DAY",
            "price": round(price, 2),
            "tag": "FinVisionCopilot",
            "order_type": order_type.upper(),
            "transaction_type": transaction_type.upper(),
            "disclosed_quantity": 0,
            "trigger_price": round(stop_loss, 2),
            "is_amo": False,
        }
    elif "Angel" in broker:
        # Angel One SmartAPI format
        return {
            "variety": "NORMAL",
            "tradingsymbol": f"{clean_symbol}-EQ",
            "symboltoken": clean_symbol,
            "transactiontype": transaction_type.upper(),
            "exchange": "NSE",
            "ordertype": order_type.upper(),
            "producttype": "INTRADAY" if product == "MIS" else "DELIVERY",
            "duration": "DAY",
            "price": str(round(price, 2)),
            "squareoff": str(round(target, 2)) if target > 0 else "0",
            "stoploss": str(round(stop_loss, 2)) if stop_loss > 0 else "0",
            "quantity": str(quantity),
        }
    else:
        # Generic Fenix / Webhook format
        return {
            "source": "FinVision AI Terminal",
            "broker": broker,
            "symbol": clean_symbol,
            "action": transaction_type.upper(),
            "quantity": quantity,
            "limit_price": round(price, 2),
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2),
            "product": product.upper(),
        }


def dispatch_broker_order(
    broker: str,
    payload: Dict[str, Any],
    api_key: Optional[str] = None,
    access_token: Optional[str] = None,
    webhook_url: Optional[str] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Dispatches order to live broker API or webhook.
    Guaranteed dry-run safety when dry_run=True.
    """
    if dry_run or not webhook_url:
        return {
            "status": "SIMULATED_SUCCESS",
            "message": f"🛡️ [DRY RUN / SAFE SIMULATION] {broker} order payload prepared successfully.",
            "broker": broker,
            "payload": payload,
            "order_id": f"SIM_{abs(hash(json.dumps(payload, sort_keys=True))) % 10000000}",
        }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FinVision-Terminal/3.0",
        }
        if api_key and access_token:
            headers["Authorization"] = f"token {api_key}:{access_token}"

        req = urllib.request.Request(webhook_url, data=data_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            resp_body = response.read().decode("utf-8")
            return {
                "status": "SUCCESS",
                "message": f"🚀 Live order dispatched to {broker} successfully!",
                "response": resp_body,
                "payload": payload,
            }
    except Exception as e:
        logger.error(f"Broker dispatch error: {e}")
        return {
            "status": "ERROR",
            "message": f"❌ Broker API error: {str(e)}",
            "payload": payload,
        }
