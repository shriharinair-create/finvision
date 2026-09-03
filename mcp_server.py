"""
finvision/mcp_server.py
=======================
Model Context Protocol (MCP) Server for FinVision v3.0.
Inspired by NSELens.

Enables Claude Desktop, Antigravity, Cursor, and other LLM clients to natively
call FinVision's quantitative trading intelligence via standard JSON-RPC 2.0 over stdio.

Usage with Claude Desktop (claude_desktop_config.json):
{
  "mcpServers": {
    "finvision": {
      "command": "python",
      "args": ["g:/AI/Stock/Stock_Claude/finvision_bkp/mcp_server.py"]
    }
  }
}
"""

from __future__ import annotations
import json
import sys
import logging
from typing import Dict, Any, List

# Suppress standard logging to stdout to keep JSON-RPC channel clean
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

import yfinance as yf
from utils.regime import detect_indian_market_regime
from utils.macro import get_live_cross_asset_macro
from utils.forecasting import compute_quantitative_confluence_forecast
from utils.gtt import compute_gtt_order_parameters
from utils.tax_calculator import compute_indian_market_friction


TOOLS_DEFINITION = [
    {
        "name": "get_market_regime",
        "description": "Returns the live Indian stock market regime (Nifty 50 trend, India VIX) and global cross-asset macro indicators (Brent Crude, USD/INR, Gold).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "analyze_stock_setup",
        "description": "Performs comprehensive institutional quantitative forecasting for an Indian stock (NSE/BSE). Returns confluence score, ML ensemble consensus, 1-Day 95% VaR & Expected Shortfall (CVaR), and entry/target/stop-loss levels.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock symbol on NSE, e.g. 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', or 'INFY'"
                },
                "forecast_days": {
                    "type": "integer",
                    "description": "Forward prediction horizon in trading days (default: 5)",
                    "default": 5
                }
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "calculate_gtt_order",
        "description": "Generates ready-to-copy Zerodha Kite, Groww, and Upstox GTT (Good-Till-Triggered) order parameters with dynamic anti-sweep stop-loss and profit targets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock symbol on NSE, e.g. 'TATAMOTORS.NS' or 'ICICIBANK'"
                },
                "shares": {
                    "type": "integer",
                    "description": "Number of shares to trade",
                    "default": 50
                }
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "calculate_indian_market_taxes",
        "description": "Calculates exact Indian regulatory turnover friction (STT, NSE exchange charges, SEBI fees, Stamp Duty, GST, and brokerage) and net take-home profit for a trade.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_price": {"type": "number", "description": "Buy price per share in INR"},
                "exit_price": {"type": "number", "description": "Sell price per share in INR"},
                "shares": {"type": "integer", "description": "Number of shares"},
                "is_intraday": {"type": "boolean", "description": "True for intraday (MIS), False for delivery (CNC)", "default": True}
            },
            "required": ["entry_price", "exit_price", "shares"]
        }
    }
]


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Executes the requested tool and returns a formatted JSON string."""
    if tool_name == "get_market_regime":
        regime = detect_indian_market_regime()
        macro = get_live_cross_asset_macro()
        return json.dumps({
            "market_regime": regime.get("regime_name"),
            "strategy_playbook": regime.get("strategy_playbook"),
            "nifty_vs_ema20_pct": regime.get("nifty_vs_ema20_pct"),
            "india_vix": regime.get("india_vix"),
            "cross_asset_macro": {
                "brent_crude": macro.get("crude_price"),
                "usd_inr": macro.get("usd_inr"),
                "gold": macro.get("gold_price"),
                "macro_stance": macro.get("macro_stance"),
            }
        }, indent=2)

    elif tool_name == "analyze_stock_setup":
        ticker = arguments.get("ticker", "").upper()
        if not ticker.endswith(".NS") and not ticker.endswith(".BO") and not ticker.startswith("^"):
            ticker += ".NS"
        days = int(arguments.get("forecast_days", 5))

        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            return json.dumps({"error": f"Unable to fetch price history for {ticker}"})

        fc = compute_quantitative_confluence_forecast(df=df, forecast_days=days)
        last_p = float(fc.get("last_price", df["Close"].iloc[-1]))
        entry_p = float(fc.get("tactical_buy_entry", last_p))
        t1 = float(fc.get("take_profit", last_p * 1.03))
        sl = float(fc.get("stop_loss", last_p * 0.98))

        return json.dumps({
            "ticker": ticker,
            "last_price": last_p,
            "recommended_action": fc.get("recommended_action"),
            "conviction": fc.get("conviction"),
            "entry_level": entry_p,
            "target1": t1,
            "stop_loss": sl,
            "risk_reward_ratio": fc.get("risk_reward_ratio"),
            "ml_consensus": fc.get("ml_ensemble", {}).get("badge"),
            "tail_risk_var_95": fc.get("tail_risk", {}).get("var_95_pct"),
            "expected_shortfall_cvar_95": fc.get("tail_risk", {}).get("cvar_95_pct"),
            "regime_adaptive_mode": fc.get("regime_adaptive_mode"),
        }, indent=2)

    elif tool_name == "calculate_gtt_order":
        ticker = arguments.get("ticker", "").upper()
        if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
            ticker += ".NS"
        shares = int(arguments.get("shares", 50))

        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty:
            return json.dumps({"error": f"Stock {ticker} not found"})

        fc = compute_quantitative_confluence_forecast(df=df)
        last_p = float(fc.get("last_price", df["Close"].iloc[-1]))
        entry_p = float(fc.get("tactical_buy_entry", last_p))
        t1 = float(fc.get("take_profit", last_p * 1.03))
        sl = float(fc.get("stop_loss", last_p * 0.98))

        gtt = compute_gtt_order_parameters(
            ticker=ticker,
            current_price=last_p,
            entry_price=entry_p,
            stop_loss=sl,
            target1=t1,
            shares=shares,
        )
        return json.dumps(gtt, indent=2)

    elif tool_name == "calculate_indian_market_taxes":
        res = compute_indian_market_friction(
            entry_price=float(arguments.get("entry_price", 0.0)),
            exit_price=float(arguments.get("exit_price", 0.0)),
            shares=int(arguments.get("shares", 1)),
            is_intraday=bool(arguments.get("is_intraday", True)),
        )
        return json.dumps(res, indent=2)

    return json.dumps({"error": f"Tool '{tool_name}' not recognized"})


def main():
    """Main JSON-RPC 2.0 loop over stdin/stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception:
            continue

        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "finvision-mcp-server",
                        "version": "3.0.0"
                    }
                }
            }
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": TOOLS_DEFINITION
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                output_text = handle_tool_call(tool_name, tool_args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": output_text}
                        ]
                    }
                }
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": f"Error executing {tool_name}: {str(e)}"}
                        ],
                        "isError": True
                    }
                }
        elif method == "notifications/initialized":
            continue
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
