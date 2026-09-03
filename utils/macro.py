"""
Macro-event tagging from real fetched news headlines.

This directly replaces the Gemini app's "Macro Regime Modifier" — which was
not connected to any real data source at all (it was manual dropdowns the
user set themselves, multiplied by hardcoded, empirically-unbacked
coefficients). This module instead classifies *actual* headlines already
being fetched for the stock (via utils.data.fetch_news) into macro
categories using keyword matching, so at least the input is real text from
the world rather than the user guessing at the answer in advance.

Honesty boundaries this module respects:
  - It does NOT claim to know about events that haven't appeared in any
    fetched headline. If there's a war and no news source mentions it in
    a headline about this stock, this module will correctly report
    "no macro signal detected" rather than inventing one.
  - It does NOT assign a numeric price-impact multiplier. Gemini's -15%/
    +12%/-10% adjustments were invented numbers with no empirical basis.
    This module only surfaces which categories are present and how many
    headlines mention them — turning "should I trust this stock's
    technicals more or less right now" into a question the user answers
    with real (if limited) information, not a fabricated coefficient.
  - It's a keyword classifier, not an NLP model — it will miss nuance and
    can mis-tag ambiguous headlines. This is disclosed in the UI, not
    hidden behind confident framing.
"""

from __future__ import annotations

import re

# Category -> keyword set. A headline can match multiple categories.
MACRO_CATEGORIES: dict[str, set[str]] = {
    "Geopolitical / Conflict": {
        "war", "conflict", "military", "invasion", "sanctions", "ceasefire",
        "missile", "border", "tension", "troops", "attack", "strike",
        "geopolitical", "embargo",
    },
    "Monetary Policy / Rates": {
        "rbi", "repo", "interest rate", "rate hike", "rate cut", "fed",
        "federal reserve", "monetary policy", "inflation", "cpi", "wpi",
        "bond yield", "central bank",
    },
    "Commodity / Energy": {
        "crude", "oil price", "opec", "gold price", "commodity",
        "natural gas", "energy crisis", "fuel price", "metal price",
    },
    "Currency / Forex": {
        "rupee", "dollar index", "forex", "currency", "depreciation",
        "appreciation", "exchange rate",
    },
    "Regulatory / Policy": {
        "sebi", "regulation", "policy change", "tariff", "duty", "ban",
        "compliance", "antitrust", "investigation", "probe",
    },
    "Weather / Agriculture": {
        "monsoon", "rainfall", "drought", "el nino", "el niño", "crop",
        "harvest", "flood", "cyclone", "agriculture ministry",
    },
    "Corporate Action": {
        "merger", "acquisition", "buyback", "stock split", "bonus issue",
        "delisting", "ipo", "stake sale", "rights issue",
    },
    "Earnings / Guidance": {
        "earnings", "quarterly results", "guidance", "profit warning",
        "revenue beat", "revenue miss", "q1 results", "q2 results",
        "q3 results", "q4 results",
    },
}


def tag_headline(headline: str) -> list[str]:
    """Returns the list of macro categories a single headline matches."""
    text = headline.lower()
    matches = []
    for category, keywords in MACRO_CATEGORIES.items():
        if any(kw in text for kw in keywords):
            matches.append(category)
    return matches


def tag_news_batch(news: list[dict]) -> dict:
    """
    Tags a batch of news items (as returned by utils.data.fetch_news) into
    macro categories, with counts and the specific matching headlines so
    the user can verify the classification themselves rather than trust a
    black-box label.

    Returns {
        'available': bool,
        'category_counts': dict[str, int],
        'category_headlines': dict[str, list[str]],
        'untagged_count': int,
        'total_headlines': int,
        'dominant_category': str | None,
        'note': str,
    }
    """
    if not news:
        return {
            "available": False,
            "category_counts": {},
            "category_headlines": {},
            "untagged_count": 0,
            "total_headlines": 0,
            "dominant_category": None,
            "note": "No news headlines available to classify.",
        }

    category_counts: dict[str, int] = {cat: 0 for cat in MACRO_CATEGORIES}
    category_headlines: dict[str, list[str]] = {cat: [] for cat in MACRO_CATEGORIES}
    untagged = 0

    for item in news:
        title = item.get("title", "") or ""
        if not title:
            continue
        matches = tag_headline(title)
        if not matches:
            untagged += 1
            continue
        for cat in matches:
            category_counts[cat] += 1
            category_headlines[cat].append(title)

    active = {k: v for k, v in category_counts.items() if v > 0}
    dominant = max(active, key=active.get) if active else None

    note = (
        "This reflects only what's present in this stock's own recently "
        "fetched headlines — it does not search the broader news cycle "
        "independently. If a major macro event hasn't been mentioned in "
        "a headline about this specific stock yet, it won't show up here."
    )

    return {
        "available": True,
        "category_counts": {k: v for k, v in category_counts.items() if v > 0},
        "category_headlines": {k: v for k, v in category_headlines.items() if v},
        "untagged_count": untagged,
        "total_headlines": len(news),
        "dominant_category": dominant,
        "note": note,
    }
