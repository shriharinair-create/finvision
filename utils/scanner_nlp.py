"""
finvision/utils/scanner_nlp.py
==============================
Entity-disambiguated NLP lookup, dynamic sector resolution, 
and Cross-Stock Catalyst Spillover engine for FinVision.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List
import chromadb
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import streamlit as st
from transformers import pipeline
import yfinance as yf

# Entity mapping with GICS Sector / Industry taxonomy and strict negative filters
TICKER_ENTITY_MAP: dict[str, dict[str, Any]] = {
    "APOLLO.NS": {
        "name": "Apollo Micro Systems",
        "keywords": ["apollo micro", "defense", "defence", "aerospace", "electronic", "missile", "radar", "drdo"],
        "negative_keywords": ["hospital", "healthcare", "pharma", "clinical", "beds", "tyre", "tire", "rubber"],
        "sector": "Industrials (Aerospace & Defense)",
    },
    "APOLLOHOSP.NS": {
        "name": "Apollo Hospitals Enterprise",
        "keywords": ["apollo hospitals", "apollo hospital", "healthcare", "clinical", "hospital beds", "pharmacy", "healthco"],
        "negative_keywords": ["micro systems", "aerospace", "defense", "defence", "tyre", "tire", "rubber"],
        "sector": "Healthcare (Hospitals & Clinics)",
    },
    "APOLLOTYRE.NS": {
        "name": "Apollo Tyres",
        "keywords": ["apollo tyres", "apollo tyre", "rubber", "automotive tyre", "oem tyre", "vredestein"],
        "negative_keywords": ["hospital", "healthcare", "micro systems", "aerospace", "defense"],
        "sector": "Consumer Cyclical (Auto Parts & Tyres)",
    },
    "RELIANCE.NS": {
        "name": "Reliance Industries",
        "keywords": ["reliance", "jio", "retail", "refining", "oil to chemical", "ambani", "green energy"],
        "negative_keywords": [],
        "sector": "Energy (Oil & Gas Integrated)",
    },
    "TCS.NS": {
        "name": "Tata Consultancy Services",
        "keywords": ["tcs", "tata consultancy", "it services", "deal wins", "cloud transformation", "ai pipeline"],
        "negative_keywords": [],
        "sector": "Technology (IT Services)",
    },
    "INFY.NS": {
        "name": "Infosys",
        "keywords": ["infosys", "it services", "attrition", "digital revenue", "salil parekh"],
        "negative_keywords": [],
        "sector": "Technology (IT Services)",
    },
    "HDFCBANK.NS": {
        "name": "HDFC Bank",
        "keywords": ["hdfc bank", "banking", "nim", "deposits", "advances", "casa ratio", "credit cards"],
        "negative_keywords": [],
        "sector": "Financial Services (Private Banks)",
    },
    "ICICIBANK.NS": {
        "name": "ICICI Bank",
        "keywords": ["icici bank", "banking", "npa", "net interest margin", "retail loan"],
        "negative_keywords": [],
        "sector": "Financial Services (Private Banks)",
    },
    "TATAMOTORS.NS": {
        "name": "Tata Motors",
        "keywords": ["tata motors", "ev", "jlr", "jaguar land rover", "commercial vehicles", "passenger vehicles"],
        "negative_keywords": [],
        "sector": "Consumer Cyclical (Auto Manufacturers)",
    },
}


@st.cache_data(ttl=86400, show_spinner=False)
def get_ticker_sector(ticker: str) -> str:
    """Dynamically resolves sector via TICKER_ENTITY_MAP with Yahoo Finance fallback."""
    if ticker in TICKER_ENTITY_MAP:
        return TICKER_ENTITY_MAP[ticker]["sector"]
    try:
        t = yf.Ticker(ticker)
        sec = t.info.get("sector")
        ind = t.info.get("industry")
        if sec and ind:
            return f"{sec} ({ind})"
        if sec:
            return sec
    except Exception:
        pass
    return "Diversified / Others"


@st.cache_resource(show_spinner=False)
def get_shared_vector_resources():
    """Cached ChromaDB client and FinBERT model handles."""
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    classifier = pipeline("text-classification", model="ProsusAI/finbert")
    client = chromadb.PersistentClient(path="./chroma_news_db")
    collection = client.get_or_create_collection(
        name="market_news",
        metadata={"hnsw:space": "cosine"},
    )
    return embedder, classifier, collection


def evaluate_ticker_sentiment_disambiguated(ticker: str, top_k: int = 3) -> dict[str, Any]:
    """Retrieves news for a ticker with entity isolation to prevent cross-contamination."""
    try:
        embedder, classifier, collection = get_shared_vector_resources()
    except Exception:
        return {
            "sentiment_score": 0.0,
            "label": "Neutral",
            "headline": "Vector DB Offline",
            "confidence": 0.0,
            "cross_impact": "None",
            "sector": get_ticker_sector(ticker),
        }

    clean_sym = ticker.replace("^", "").replace(".NS", "").replace(".BO", "")
    info = TICKER_ENTITY_MAP.get(
        ticker,
        {
            "name": clean_sym,
            "keywords": [clean_sym.lower()],
            "negative_keywords": [],
            "sector": get_ticker_sector(ticker),
        },
    )

    total_count = collection.count()
    if total_count == 0:
        return {
            "sentiment_score": 0.0,
            "label": "Neutral",
            "headline": "No news indexed in DB",
            "confidence": 0.0,
            "cross_impact": "None",
            "sector": info["sector"],
        }

    # Query using disambiguated company name and domain keywords
    query_str = f"{info['name']} {ticker} {' '.join(info['keywords'][:4])} quarterly financial guidance"
    query_vec = embedder.encode([query_str], convert_to_numpy=True).tolist()

    results = collection.query(query_embeddings=query_vec, n_results=min(15, total_count))
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []

    if not docs:
        return {
            "sentiment_score": 0.0,
            "label": "Neutral",
            "headline": "No matching articles",
            "confidence": 0.0,
            "cross_impact": "None",
            "sector": info["sector"],
        }

    # Apply strict negative keyword filters to eliminate false-positive substring collisions
    filtered_docs = []
    filtered_metas = []

    for doc, meta in zip(docs, metas):
        text_lower = doc.lower()

        # Reject if document contains negative blacklist keywords for this specific entity
        if any(neg_kw in text_lower for neg_kw in info.get("negative_keywords", [])):
            continue

        # Accept if document contains positive entity keyword or clean ticker identifier
        if any(kw in text_lower for kw in info["keywords"]) or clean_sym.lower() in text_lower:
            filtered_docs.append(doc)
            filtered_metas.append(meta)

    eval_docs = filtered_docs[:top_k] if filtered_docs else docs[:1]
    eval_metas = filtered_metas[:top_k] if filtered_metas else metas[:1]

    preds = classifier(eval_docs)
    score_weights = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
    scores = [score_weights.get(p["label"].lower(), 0.0) * float(p["score"]) for p in preds]
    avg_score = float(np.mean(scores)) if scores else 0.0

    best_pred = preds[0]
    best_meta = eval_metas[0] if eval_metas else {}

    spillover_note = "Direct Entity Match" if filtered_docs else "Macro / Sector Spillover"

    return {
        "sentiment_score": round(avg_score, 2),
        "label": best_pred["label"].capitalize(),
        "confidence": round(float(best_pred["score"]) * 100, 1),
        "headline": best_meta.get("title", eval_docs[0][:65]),
        "source": best_meta.get("source", "ChromaDB"),
        "cross_impact": spillover_note,
        "sector": info["sector"],
    }


# Backwards compatibility alias
evaluate_ticker_sentiment_fast = evaluate_ticker_sentiment_disambiguated