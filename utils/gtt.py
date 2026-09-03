"""
finvision/utils/gtt.py
======================
Automated GTT (Good-Till-Triggered) Order Math for Zerodha Kite, Upstox, & Groww.
Computes precise trigger offsets, limit prices, and OCO (One-Cancels-Other) targets/stops
formatted for 1-click copy-pasting into Indian discount brokers.
"""

from __future__ import annotations
from typing import Dict, Any


def compute_gtt_order_parameters(
    ticker: str,
    current_price: float,
    entry_price: float,
    stop_loss: float,
    target1: float,
    target2: float = 0.0,
    shares: int = 1,
    is_intraday: bool = False,
) -> Dict[str, Any]:
    """
    Calculates ready-to-copy GTT order triggers and limit parameters.
    
    Zerodha/Groww GTT Rules:
      - Single GTT: Triggers a BUY order when price hits trigger price.
        Trigger price should be slightly above entry limit (e.g. +0.20%) so the limit order
        is placed into the exchange order book right before execution.
      - OCO GTT (Two-leg): Placed after buying to set Stop Loss AND Target simultaneously.
        When one leg executes, the broker automatically cancels the other leg.
    """
    clean_ticker = ticker.replace(".NS", "").replace(".BO", "")
    
    # 1. Single GTT: Buy Limit Entry Setup
    # Trigger slightly higher (0.15% to 0.25%) to ensure activation
    trigger_buffer_pct = 0.0020  # 0.20%
    if entry_price >= current_price:
        # Momentum breakout buy
        buy_trigger = round(entry_price * (1.0 - trigger_buffer_pct), 2)
    else:
        # Dip buy near support
        buy_trigger = round(entry_price * (1.0 + trigger_buffer_pct), 2)
    
    buy_limit = round(entry_price, 2)

    # 2. OCO GTT Leg 1: Stop Loss Trigger & Limit
    # Trigger placed 0.20% above the stop loss price so market order/limit triggers in time
    sl_trigger = round(stop_loss * (1.0 + trigger_buffer_pct), 2)
    sl_limit = round(stop_loss, 2)
    sl_pct = round(((stop_loss - entry_price) / entry_price) * 100.0, 2)

    # 3. OCO GTT Leg 2: Target 1 Trigger & Limit
    # Trigger placed 0.20% below target so limit order is pre-loaded on exchange
    tgt1_trigger = round(target1 * (1.0 - trigger_buffer_pct), 2)
    tgt1_limit = round(target1, 2)
    tgt1_pct = round(((target1 - entry_price) / entry_price) * 100.0, 2)

    # Formatted copy strings for Zerodha Kite / Groww mobile apps
    copy_single_gtt = (
        f"GTT BUY {clean_ticker}\n"
        f"Trigger: ₹{buy_trigger:,.2f}\n"
        f"Limit Price: ₹{buy_limit:,.2f}\n"
        f"Qty: {shares}"
    )

    copy_oco_gtt = (
        f"GTT OCO {clean_ticker}\n"
        f"[STOP-LOSS]\n"
        f"Trigger: ₹{sl_trigger:,.2f} ({sl_pct:+.1f}%)\n"
        f"Price: ₹{sl_limit:,.2f}\n"
        f"[TARGET 1]\n"
        f"Trigger: ₹{tgt1_trigger:,.2f} ({tgt1_pct:+.1f}%)\n"
        f"Price: ₹{tgt1_limit:,.2f}\n"
        f"Qty: {shares}"
    )

    return {
        "ticker": clean_ticker,
        "shares": shares,
        "single_gtt": {
            "trigger_price": buy_trigger,
            "limit_price": buy_limit,
            "order_type": "LIMIT",
            "transaction_type": "BUY",
            "copy_text": copy_single_gtt,
        },
        "oco_gtt": {
            "sl_trigger_price": sl_trigger,
            "sl_limit_price": sl_limit,
            "sl_pct": sl_pct,
            "target_trigger_price": tgt1_trigger,
            "target_limit_price": tgt1_limit,
            "target_pct": tgt1_pct,
            "target2_price": round(target2, 2) if target2 > 0 else None,
            "copy_text": copy_oco_gtt,
        },
        "instructions": [
            f"1. In Zerodha/Groww, search '{clean_ticker}' and tap 'Create GTT'.",
            f"2. For Entry: Set Trigger at ₹{buy_trigger:,.2f} and Price at ₹{buy_limit:,.2f}.",
            f"3. Once executed, create an OCO GTT: Stop-loss trigger ₹{sl_trigger:,.2f} and Target trigger ₹{tgt1_trigger:,.2f}.",
            f"4. GTT stays active for 1 full year until triggered or manually cancelled."
        ]
    }
