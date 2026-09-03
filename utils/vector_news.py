"""
finvision/utils/vector_news.py
==============================
Vector store and NLP catalyst engine for FinVision.
Integrates ChromaDB, Sentence-Transformers, and FinBERT.
"""

from __future__ import annotations

import datetime
import hashlib
from typing import Any, Dict, List

import chromadb
import feedparser
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
import streamlit as st
from transformers import pipeline

# Diverse RSS endpoints with Google News backup feeds for Indian Stock Markets
RSS_FEEDS: dict[str, str] = {
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "Livemint": "https://www.livemint.com/rss/markets",
    "Google News (Nifty)": "https://news.google.com/rss/search?q=Nifty+50+NSE+Stock+Market+India&hl=en-IN&gl=IN&ceid=IN:en",
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


@st.cache_resource(show_spinner="Loading Vector & FinBERT Models...")
def get_vector_resources():
    """Load and cache embedding model, FinBERT pipeline, and ChromaDB client."""
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    classifier = pipeline("text-classification", model="ProsusAI/finbert")
    client = chromadb.PersistentClient(path="./chroma_news_db")
    collection = client.get_or_create_collection(
        name="market_news",
        metadata={"hnsw:space": "cosine"},
    )
    return embedder, classifier, collection


def get_collection_count() -> int:
    """Return total number of indexed news embeddings in ChromaDB."""
    try:
        _, _, collection = get_vector_resources()
        return collection.count()
    except Exception:
        return 0


def ingest_live_news() -> int:
    """Fetch live market news using browser headers and index them into ChromaDB."""
    embedder, _, collection = get_vector_resources()
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            # Fetch via requests with browser headers to prevent 403 Forbidden blocks
            resp = requests.get(feed_url, headers=BROWSER_HEADERS, timeout=8)
            if resp.status_code != 200:
                continue

            parsed = feedparser.parse(resp.content)
            for entry in parsed.entries[:25]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", title).strip()
                link = entry.get("link", "")
                pub_date = entry.get("published", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

                if not title or len(title) < 10:
                    continue

                # Clean basic HTML tags from summary if present
                clean_summary = summary.replace("<p>", "").replace("</p>", "").replace("<b>", "").replace("</b>", "")
                doc_text = f"{title}. {clean_summary}"
                
                # Deterministic ID based on content
                doc_id = hashlib.md5((link or title).encode("utf-8")).hexdigest()

                # Deduplication check
                existing = collection.get(ids=[doc_id])
                if not existing["ids"]:
                    documents.append(doc_text)
                    metadatas.append({
                        "source": source_name,
                        "title": title,
                        "url": link,
                        "timestamp": str(pub_date),
                    })
                    ids.append(doc_id)
        except Exception as e:
            continue

    if documents:
        embeddings = embedder.encode(documents, convert_to_numpy=True).tolist()
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    try:
        from utils.bse_corporate import ingest_bse_filings_to_vector_news
        ingest_bse_filings_to_vector_news()
    except Exception:
        pass

    return len(documents)


def get_sentiment_context(query_str: str = "Nifty 50 macro economic market sentiment", n_results: int = 5) -> dict[str, Any]:
    """Retrieve top-k relevant news articles and compute composite FinBERT sentiment scores."""
    embedder, classifier, collection = get_vector_resources()

    if collection.count() == 0:
        ingest_live_news()

    total_count = collection.count()
    if total_count == 0:
        return {
            "sentiment_score": 0.0,
            "bullish_pct": 50.0,
            "articles": [],
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
        }

    k = min(n_results, total_count)
    query_vec = embedder.encode([query_str], convert_to_numpy=True).tolist()
    results = collection.query(query_embeddings=query_vec, n_results=k)

    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []

    if not docs:
        return {
            "sentiment_score": 0.0,
            "bullish_pct": 50.0,
            "articles": [],
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
        }

    predictions = classifier(docs)
    score_weights = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

    numeric_scores = []
    pos_count, neg_count, neu_count = 0, 0, 0
    articles_out = []

    for meta, pred in zip(metas, predictions):
        label = pred["label"].lower()
        conf = float(pred["score"])
        numeric_scores.append(score_weights.get(label, 0.0) * conf)

        if label == "positive":
            pos_count += 1
        elif label == "negative":
            neg_count += 1
        else:
            neu_count += 1

        art = dict(meta)
        art["sentiment_label"] = label.capitalize()
        art["sentiment_confidence"] = round(conf * 100, 1)
        articles_out.append(art)

    avg_score = float(np.mean(numeric_scores)) if numeric_scores else 0.0
    total_analyzed = len(docs)
    bullish_pct = (pos_count / total_analyzed) * 100 if total_analyzed > 0 else 50.0

    return {
        "sentiment_score": avg_score,
        "bullish_pct": bullish_pct,
        "articles": articles_out,
        "positive_count": pos_count,
        "negative_count": neg_count,
        "neutral_count": neu_count,
    }