"""
글로벌 뉴스 수집.
NEWSAPI_KEY 환경변수가 있으면 NewsAPI 사용, 없으면 yfinance 내장 뉴스 사용.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone

import requests
import yfinance as yf

logger = logging.getLogger(__name__)

NEWS_TICKERS = ["^GSPC", "NVDA", "TSM", "^TNX"]
NEWSAPI_URL  = "https://newsapi.org/v2/everything"


def _fetch_newsapi(query: str, api_key: str, hours: int = 20) -> list[dict]:
    from_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "q":        query,
        "from":     from_time,
        "sortBy":   "relevancy",
        "language": "en",
        "pageSize": 5,
        "apiKey":   api_key,
    }
    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {"title": a["title"], "source": a["source"]["name"], "url": a["url"]}
            for a in articles
        ]
    except Exception as e:
        logger.warning("NewsAPI 요청 실패 (%s): %s", query, e)
        return []


def _fetch_yfinance_news(symbols: list[str]) -> list[dict]:
    seen   = set()
    result = []
    for sym in symbols:
        try:
            news = yf.Ticker(sym).news or []
            for item in news[:3]:
                title = item.get("title", "")
                if title and title not in seen:
                    seen.add(title)
                    result.append({
                        "title":  title,
                        "source": item.get("publisher", ""),
                        "url":    item.get("link", ""),
                    })
        except Exception as e:
            logger.debug("%s 뉴스 조회 실패: %s", sym, e)
    return result


def fetch_news() -> dict[str, list[dict]]:
    """
    {macro: [...], semicon: [...], market: [...]} 형태로 반환.
    각 항목은 {title, source, url}.
    """
    api_key = os.environ.get("NEWSAPI_KEY", "")

    if api_key:
        logger.info("NewsAPI 사용")
        return {
            "market":  _fetch_newsapi("US stock market S&P500 Fed", api_key),
            "macro":   _fetch_newsapi("interest rate inflation dollar economy", api_key),
            "semicon": _fetch_newsapi("semiconductor NVIDIA TSMC AI chip", api_key),
        }
    else:
        logger.info("yfinance 내장 뉴스 사용 (NEWSAPI_KEY 미설정)")
        all_news = _fetch_yfinance_news(NEWS_TICKERS)
        third    = max(1, len(all_news) // 3)
        return {
            "market":  all_news[:third],
            "macro":   all_news[third:third*2],
            "semicon": all_news[third*2:],
        }
