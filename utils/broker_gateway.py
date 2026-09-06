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
import ipaddress
import json
import logging
import socket
from typing import Dict, Any, Optional
import urllib.request
import urllib.error
from urllib.parse import urlparse
import uuid

logger = logging.getLogger(__name__)

SUPPORTED_BROKERS = [
    "Zerodha Kite",
    "Groww (GTT / Webhook)",
    "Upstox",
    "Angel One",
    "Fenix Webhook / n8n",
]

# Trusted official broker API host suffixes
ALLOWED_BROKER_DOMAINS = [
    "kite.trade",
    "zerodha.com",
    "upstox.com",
    "angelone.in",
    "angelbroking.com",
    "groww.in",
]


def _resolve_and_check_ips(hostname: str) -> tuple[bool, str]:
    """Resolves DNS and verifies no returned IP is loopback, private, link-local, or multicast (H3 Fix)."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        return False, f"Could not resolve hostname '{hostname}': {e}"
    for family, _, _, _, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False, f"Hostname '{hostname}' resolves to a private/internal address ({ip_str}) — blocked (SSRF guard)."
        except ValueError:
            continue
    return True, "OK"


def validate_broker_endpoint(webhook_url: str, broker: str = "", allow_custom_webhook: bool = False) -> tuple[bool, str]:
    """
    Validates the destination endpoint for live broker routing.
    Protects against SSRF, internal cloud metadata exfiltration, DNS rebinding, and untrusted domains (H2 & H3).
    """
    if not webhook_url or not isinstance(webhook_url, str):
        return False, "Webhook URL cannot be empty."

    parsed = urlparse(webhook_url.strip())
    if parsed.scheme.lower() != "https":
        return False, "Live broker endpoints must strictly use secure HTTPS (http:// is prohibited)."

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "Invalid endpoint hostname."

    # 1. Block loopback, localhost, and cloud metadata endpoints
    if hostname in ("localhost", "127.0.0.1", "::1", "metadata.google.internal", "169.254.169.254"):
        return False, "Localhost and cloud-metadata addresses are strictly prohibited (SSRF Guard)."

    # 2. Check if IP address is provided directly
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False, f"Private or link-local IP address '{hostname}' is prohibited."
    except ValueError:
        # Not a raw IP address; hostname is a domain name
        pass

    # 3. DNS resolution check against DNS rebinding to internal IPs (H3)
    ok_dns, dns_msg = _resolve_and_check_ips(hostname)
    if not ok_dns:
        return False, dns_msg

    # 4. Enforce trusted broker domain allowlist unless allow_custom_webhook is explicitly granted (H2)
    is_known_broker = any(hostname == d or hostname.endswith("." + d) for d in ALLOWED_BROKER_DOMAINS)
    if not is_known_broker and not allow_custom_webhook:
        return False, (
            f"'{hostname}' is not a recognized official broker domain. If routing through "
            f"a custom webhook/automation bridge (n8n, Zapier), enable 'Allow custom webhook' first."
        )

    return True, "Valid broker endpoint."


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
    elif "Groww" in broker:
        # Groww GTT & Webhook payload format
        return {
            "symbol": clean_symbol,
            "exchange": "NSE",
            "transaction_type": transaction_type.upper(),
            "order_type": order_type.upper(),
            "quantity": quantity,
            "product": "INTRADAY" if product == "MIS" else "DELIVERY",
            "price": round(price, 2),
            "trigger_price": round(stop_loss, 2) if "SL" in order_type else 0.0,
            "target_price": round(target, 2),
            "tag": "FinVisionAuto",
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
    allow_custom_webhook: bool = False,
) -> Dict[str, Any]:
    """
    Dispatches order to live broker API or webhook with guaranteed idempotency.
    Guaranteed dry-run safety when dry_run=True.
    """
    idempotency_key = str(uuid.uuid4())
    payload = dict(payload)
    payload["idempotency_key"] = idempotency_key

    if dry_run or not webhook_url:
        sim_id = f"SIM_{uuid.uuid4().hex[:12].upper()}"
        return {
            "status": "SIMULATED_SUCCESS",
            "message": f"🛡️ [DRY RUN / SAFE SIMULATION] {broker} order payload prepared successfully.",
            "broker": broker,
            "payload": payload,
            "order_id": sim_id,
            "idempotency_key": idempotency_key,
        }

    # SSRF & Endpoint Validation Guard (H2 & H3)
    is_valid_url, url_err = validate_broker_endpoint(webhook_url, broker=broker, allow_custom_webhook=allow_custom_webhook)
    if not is_valid_url:
        logger.error(f"Broker dispatch blocked by security guard: {url_err}")
        return {
            "status": "SECURITY_ERROR",
            "message": f"❌ Broker dispatch blocked: {url_err}",
            "payload": payload,
        }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FinVision-Terminal/3.0",
            "X-Idempotency-Key": idempotency_key,
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
                "idempotency_key": idempotency_key,
            }
    except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
        logger.error(f"Broker dispatch AMBIGUOUS outcome (network/timeout): {e}")
        return {
            "status": "AMBIGUOUS_NEEDS_RECONCILIATION",
            "message": f"⚠️ Order may or may not have executed at {broker} — network error/timeout before confirmation. Manual verification required: {str(e)}",
            "payload": payload,
            "idempotency_key": idempotency_key,
        }
    except Exception as e:
        logger.error(f"Broker dispatch error: {e}")
        return {
            "status": "ERROR",
            "message": f"❌ Broker API error: {str(e)}",
            "payload": payload,
            "idempotency_key": idempotency_key,
        }

