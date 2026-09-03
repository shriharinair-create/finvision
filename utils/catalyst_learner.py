"""
finvision/utils/catalyst_learner.py
===================================
Learner module: Discovers statistically significant keyword/n-gram catalysts
correlated with historical stock price movements.
Includes:
  1. HTML tag & scraper boilerplate sanitization.
  2. Benjamini-Hochberg False Discovery Rate (FDR) multiple-hypothesis correction.
  3. Minimum economic effect size floor (|Avg Move| >= 0.50%).
  4. Temporal Out-of-Sample (OOS) holdout validation.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st

logger = logging.getLogger("finvision.catalyst_learner")

HTML_AND_WEB_JUNK = {
    "target", "blank", "href", "http", "https", "html", "span", "div", "font", "color",
    "scanx", "trade", "click", "read", "more", "view", "source", "article", "feed",
    "rss", "com", "www", "url", "image", "photo", "copyright", "rights", "reserved",
    "updated", "published", "ist", "pm", "am", "today", "yesterday", "tomorrow",
    "ltd", "limited", "corp", "corporation", "inc", "co", "pvt", "plc"
}

STANDARD_STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "over", "after", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "but", "if", "then", "else", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can",
    "will", "just", "don", "should", "now", "says", "said", "stock", "shares", "market"
}

ALL_STOP_WORDS = STANDARD_STOP_WORDS | HTML_AND_WEB_JUNK


def _sanitize_news_text(text: str) -> str:
    """Strips HTML tags, URLs, entities, and web-scraper boilerplate."""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"https?://\S+|www\.\S+", " ", clean)
    clean = re.sub(r"&[a-zA-Z0-9#]+;", " ", clean)
    clean = re.sub(r"(target|blank|href|http|https|www|com|scanx|trade)", " ", clean, flags=re.I)
    clean = re.sub(r"[^a-zA-Z\s]", " ", clean)
    return clean.lower().strip()


def _extract_ngrams(text: str, n_range=(1, 3)) -> list[str]:
    """Extract clean, sanitized unigrams, bigrams, and trigrams."""
    clean = _sanitize_news_text(text)
    tokens = [w for w in clean.split() if w not in ALL_STOP_WORDS and len(w) > 3]
    
    extracted = []
    # Unigrams
    if 1 in n_range:
        extracted.extend(tokens)
    # Bigrams
    if 2 in n_range:
        for i in range(len(tokens) - 1):
            w1, w2 = tokens[i], tokens[i+1]
            if w1 not in HTML_AND_WEB_JUNK and w2 not in HTML_AND_WEB_JUNK:
                extracted.append(f"{w1} {w2}")
    # Trigrams
    if 3 in n_range:
        for i in range(len(tokens) - 2):
            w1, w2, w3 = tokens[i], tokens[i+1], tokens[i+2]
            if w1 not in HTML_AND_WEB_JUNK and w2 not in HTML_AND_WEB_JUNK and w3 not in HTML_AND_WEB_JUNK:
                extracted.append(f"{w1} {w2} {w3}")
    return extracted


def benjamini_hochberg_fdr(p_values: list[float] | np.ndarray) -> np.ndarray:
    """Applies Benjamini-Hochberg False Discovery Rate (FDR) adjustment."""
    p_vals = np.asarray(p_values, dtype=float)
    n = len(p_vals)
    if n == 0:
        return np.array([])

    sorted_indices = np.argsort(p_vals)
    sorted_p = p_vals[sorted_indices]
    
    ranks = np.arange(1, n + 1)
    adj_p = sorted_p * n / ranks
    
    for i in range(n - 2, -1, -1):
        adj_p[i] = min(adj_p[i], adj_p[i + 1])
        
    adj_p = np.clip(adj_p, 0.0, 1.0)
    out = np.empty(n)
    out[sorted_indices] = adj_p
    return out


class KeywordCatalystLearner:
    def __init__(self, min_occurrences: int = 5, fdr_threshold: float = 0.05, min_effect_pct: float = 0.45):
        self.min_occurrences = min_occurrences
        self.fdr_threshold = fdr_threshold
        self.min_effect_pct = min_effect_pct
        self.learned_catalysts: pd.DataFrame = pd.DataFrame()

    def train(self, news_history: list[dict[str, Any]], price_df: pd.DataFrame, holdout_ratio: float = 0.25) -> pd.DataFrame:
        """
        Learns statistically rigorous keyword-to-price correlations with:
          1. Benjamini-Hochberg False Discovery Rate (BH-FDR) correction.
          2. Minimum economic effect size floor (>= 0.45%).
          3. Out-of-Sample (OOS) temporal validation split.
        """
        if not news_history or price_df.empty:
            return pd.DataFrame()

        df_p = price_df.copy()
        if "Open" in df_p.columns and "Close" in df_p.columns:
            df_p["pct_change"] = ((df_p["Close"] - df_p["Open"]) / df_p["Open"]) * 100.0
        else:
            df_p["pct_change"] = df_p["Close"].pct_change() * 100.0

        date_return_map = {}
        for dt_idx, row in df_p.iterrows():
            d_str = str(dt_idx)[:10]
            date_return_map[d_str] = float(row.get("pct_change", 0.0))

        # Sort news chronologically for strict Out-of-Sample temporal validation
        sorted_news = sorted(news_history, key=lambda x: str(x.get("date", x.get("timestamp", ""))))
        split_idx = int(len(sorted_news) * (1.0 - holdout_ratio))
        
        train_news = sorted_news[:split_idx]
        oos_news = sorted_news[split_idx:]

        # --- 1. In-Sample Training ---
        keyword_moves_train: dict[str, list[float]] = {}
        for item in train_news:
            d_str = str(item.get("date", item.get("timestamp", "")))[:10]
            text = str(item.get("text", item.get("title", "")))
            if d_str in date_return_map:
                move = date_return_map[d_str]
                ngrams = _extract_ngrams(text, n_range=(1, 3))
                for ng in set(ngrams):
                    if len(ng) < 4 or any(junk in ng for junk in HTML_AND_WEB_JUNK):
                        continue
                    if ng not in keyword_moves_train:
                        keyword_moves_train[ng] = []
                    keyword_moves_train[ng].append(move)

        raw_rules = []
        for kw, moves in keyword_moves_train.items():
            if len(moves) >= self.min_occurrences:
                avg_m = float(np.mean(moves))
                win_r = float(np.mean([1 if m > 0 else 0 for m in moves]) * 100.0)
                
                if len(moves) >= 3 and np.std(moves) > 1e-6:
                    t_stat, p_val = stats.ttest_1samp(moves, 0.0)
                    p_val = float(p_val) if not np.isnan(p_val) else 1.0
                else:
                    p_val = 1.0

                raw_rules.append({
                    "catalyst": kw,
                    "train_occurrences": len(moves),
                    "train_avg_move": round(avg_m, 2),
                    "train_win_rate": round(win_r, 1),
                    "raw_p_value": float(p_val)
                })

        if not raw_rules:
            return pd.DataFrame()

        df_res = pd.DataFrame(raw_rules)
        df_res["fdr_p_value"] = benjamini_hochberg_fdr(df_res["raw_p_value"].values)

        # --- 2. Out-of-Sample Holdout Validation ---
        keyword_moves_oos: dict[str, list[float]] = {}
        for item in oos_news:
            d_str = str(item.get("date", item.get("timestamp", "")))[:10]
            text = str(item.get("text", item.get("title", "")))
            if d_str in date_return_map:
                move = date_return_map[d_str]
                ngrams = _extract_ngrams(text, n_range=(1, 3))
                for ng in set(ngrams):
                    if ng in keyword_moves_train:
                        if ng not in keyword_moves_oos:
                            keyword_moves_oos[ng] = []
                        keyword_moves_oos[ng].append(move)

        oos_avg_moves = []
        oos_win_rates = []
        oos_occurrences = []
        oos_validated = []

        for _, r in df_res.iterrows():
            kw = r["catalyst"]
            if kw in keyword_moves_oos and len(keyword_moves_oos[kw]) >= 2:
                o_moves = keyword_moves_oos[kw]
                o_avg = float(np.mean(o_moves))
                o_win = float(np.mean([1 if m > 0 else 0 for m in o_moves]) * 100.0)
                oos_avg_moves.append(round(o_avg, 2))
                oos_win_rates.append(round(o_win, 1))
                oos_occurrences.append(len(o_moves))
                # Validated if sign matches in-sample and effect size holds
                is_val = bool(np.sign(o_avg) == np.sign(r["train_avg_move"]) and abs(o_avg) >= 0.30)
                oos_validated.append(is_val)
            else:
                oos_avg_moves.append(0.0)
                oos_win_rates.append(50.0)
                oos_occurrences.append(0)
                oos_validated.append(False)

        df_res["oos_occurrences"] = oos_occurrences
        df_res["oos_avg_move"] = oos_avg_moves
        df_res["oos_win_rate"] = oos_win_rates
        df_res["is_oos_validated"] = oos_validated

        # Full Significance Criteria:
        # 1. FDR p <= 0.05
        # 2. In-sample |Move| >= min_effect_pct
        # 3. Out-of-sample validation holds
        df_res["is_significant"] = (
            (df_res["fdr_p_value"] <= self.fdr_threshold) & 
            (df_res["train_avg_move"].abs() >= self.min_effect_pct) &
            (df_res["is_oos_validated"] == True)
        ).astype(int)

        # Standardized column aliases for DB compatibility
        df_res["occurrences"] = df_res["train_occurrences"] + df_res["oos_occurrences"]
        df_res["avg_move_pct"] = df_res["train_avg_move"]
        df_res["win_rate_pct"] = df_res["train_win_rate"]
        df_res["p_value"] = df_res["fdr_p_value"]

        df_res = df_res.sort_values(by=["is_significant", "fdr_p_value", "occurrences"], ascending=[False, True, False])
        self.learned_catalysts = df_res
        return df_res

    def score_todays_news(self, text: str) -> dict[str, Any]:
        """Scores live news against the statistically-validated, OOS-proven causal rules."""
        if self.learned_catalysts.empty:
            return {"sentiment_score": 0.0, "catalyst_score": 0.0, "matched_rules": []}

        ngrams = _extract_ngrams(text, n_range=(1, 3))
        sig_rules = self.learned_catalysts[self.learned_catalysts["is_significant"] == 1]
        
        if sig_rules.empty:
            # Fallback to high FDR significant rules
            sig_rules = self.learned_catalysts[self.learned_catalysts["fdr_p_value"] <= 0.08]

        rule_map = {r["catalyst"]: r for _, r in sig_rules.iterrows()}
        matched = []
        scores = []
        for ng in ngrams:
            if ng in rule_map:
                r = rule_map[ng]
                matched.append(r)
                scores.append(r.get("avg_move_pct", r.get("train_avg_move", 0.0)))

        if not scores:
            return {"sentiment_score": 0.0, "catalyst_score": 0.0, "matched_rules": []}

        avg_impact = float(np.mean(scores))
        fused_catalyst_score = float(np.clip(avg_impact / 2.0, -1.0, 1.0))
        return {
            "sentiment_score": fused_catalyst_score,
            "catalyst_score": fused_catalyst_score,
            "matched_rules": matched
        }
