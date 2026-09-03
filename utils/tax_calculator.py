"""
finvision/utils/tax_calculator.py
==================================
Indian Stock Market Regulatory Charges & Net Take-Home Profit Engine.
Accurately computes:
  1. Securities Transaction Tax (STT) - 0.025% on Intraday equity sell; 0.1% on delivery (both legs)
  2. Exchange Turnover Charges - NSE 0.00297% (~0.003%) of turnover
  3. Goods & Services Tax (GST) - 18% on (Brokerage + Exchange Txn Charges + SEBI fees)
  4. SEBI Turnover Charges - ₹10 per crore (0.0001%)
  5. Stamp Duty - 0.003% on Buy side turnover (intraday) or 0.015% (delivery)
  6. Brokerage - Flat ₹20 per executed order (or 0.03% whichever is lower) -> ₹40 round trip
"""

from __future__ import annotations
from typing import Dict, Any


def compute_indian_market_friction(
    entry_price: float,
    exit_price: float,
    shares: int,
    is_intraday: bool = True,
    flat_brokerage_per_order: float = 20.0,
) -> Dict[str, Any]:
    """
    Computes exact regulatory taxes, exchange fees, brokerage, and net profit.
    
    Args:
        entry_price: Buy price per share in INR.
        exit_price: Target or sell price per share in INR.
        shares: Number of shares traded.
        is_intraday: True for intraday equity (MIS), False for delivery (CNC).
        flat_brokerage_per_order: Flat discount broker fee per leg (default ₹20 for Zerodha/Groww).
    
    Returns:
        Dictionary with gross profit, detailed fee breakdown, net profit, and break-even price.
    """
    if shares <= 0 or entry_price <= 0:
        return {
            "gross_profit": 0.0,
            "total_friction": 0.0,
            "net_profit": 0.0,
            "net_return_pct": 0.0,
            "break_even_price": entry_price,
            "friction_breakdown": {}
        }

    buy_turnover = round(entry_price * shares, 2)
    sell_turnover = round(exit_price * shares, 2)
    total_turnover = round(buy_turnover + sell_turnover, 2)
    gross_profit = round((exit_price - entry_price) * shares, 2)

    # 1. Brokerage (Zerodha/Groww standard: ₹20 or 0.03% whichever is lower per order)
    if is_intraday:
        buy_brokerage = min(flat_brokerage_per_order, round(buy_turnover * 0.0003, 2))
        sell_brokerage = min(flat_brokerage_per_order, round(sell_turnover * 0.0003, 2))
    else:
        buy_brokerage = 0.0  # Zero brokerage on delivery for Zerodha/Groww
        sell_brokerage = 0.0
    total_brokerage = round(buy_brokerage + sell_brokerage, 2)

    # 2. STT (Securities Transaction Tax)
    # Intraday: 0.025% on sell turnover only
    # Delivery: 0.1% on both buy and sell turnover
    if is_intraday:
        stt = round(sell_turnover * 0.00025, 2)
    else:
        stt = round(total_turnover * 0.001, 2)

    # 3. Exchange Turnover Charges (NSE: ~0.00297%)
    exchange_charges = round(total_turnover * 0.0000297, 2)

    # 4. Stamp Duty (Payable only on Buy turnover: 0.003% intraday, 0.015% delivery)
    stamp_duty_rate = 0.00003 if is_intraday else 0.00015
    stamp_duty = round(buy_turnover * stamp_duty_rate, 2)

    # 5. SEBI Turnover Charges (₹10 / crore = 0.0001% of total turnover)
    sebi_charges = round(total_turnover * 0.000001, 2)

    # 6. GST (18% on Brokerage + Exchange Charges + SEBI Charges)
    gst = round((total_brokerage + exchange_charges + sebi_charges) * 0.18, 2)

    # Total regulatory and execution friction
    total_friction = round(total_brokerage + stt + exchange_charges + stamp_duty + sebi_charges + gst, 2)
    net_profit = round(gross_profit - total_friction, 2)
    net_return_pct = round((net_profit / buy_turnover) * 100.0, 2) if buy_turnover > 0 else 0.0

    # Break-even price (approximate exit price needed to have ₹0 net profit)
    # Price difference needed to cover total friction per share
    points_to_breakeven = total_friction / shares if shares > 0 else 0.0
    break_even_price = round(entry_price + points_to_breakeven, 2)

    return {
        "gross_profit": gross_profit,
        "total_friction": total_friction,
        "net_profit": net_profit,
        "net_return_pct": net_return_pct,
        "break_even_price": break_even_price,
        "points_to_breakeven": round(points_to_breakeven, 2),
        "friction_breakdown": {
            "brokerage": total_brokerage,
            "stt": stt,
            "exchange_charges": exchange_charges,
            "gst": gst,
            "stamp_duty": stamp_duty,
            "sebi_charges": sebi_charges,
        }
    }
