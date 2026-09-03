"""
finvision/utils/user_prefs.py
=============================
Persistent user settings & profile store (Budget, Risk, Goal).
Saved to local JSON storage so settings survive page reloads and app restarts.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

PREFS_FILE = Path(__file__).resolve().parent.parent / "data" / "user_preferences.json"

DEFAULT_PREFS = {
    "total_capital": 500000.0,
    "risk_profile": "Balanced (1.0% max risk)",
    "risk_pct": 0.01,
    "trading_goal_index": 0,
}


def get_user_preferences() -> dict[str, Any]:
    """Loads saved user preferences from disk."""
    if PREFS_FILE.exists():
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = dict(DEFAULT_PREFS)
                res.update(data)
                return res
        except Exception:
            pass
    return dict(DEFAULT_PREFS)


def save_user_preference(key: str, value: Any) -> None:
    """Updates and saves a specific preference to disk."""
    prefs = get_user_preferences()
    prefs[key] = value
    try:
        PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
    except Exception:
        pass
