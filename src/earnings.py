"""
전날 실적 발표 종목 수집.
주요 종목 리스트를 체크해 earnings_dates 에서 어제 날짜 항목을 찾는다.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import yfinance as yf

logger = logging.getLogger(__name__)

WATCHLIST = [
    # 빅테크
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NFLX",
    # 반도체
    "NVDA", "AMD", "INTC", "TSM", "ASML", "AMAT", "MU", "QCOM", "AVGO", "TXN", "KLAC", "LRCX",
    # 금융
    "JPM", "GS", "BAC", "MS",
    # 기타 주요 종목
    "ORCL", "CRM", "ADBE", "IBM", "PYPL", "V", "MA",
]


def fetch_yesterday_earnings() -> list[dict]:
    """어제 실적 발표한 종목 리스트 반환."""
    now       = datetime.now(timezone.utc)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    results: list[dict] = []

    for sym in WATCHLIST:
        try:
            ticker = yf.Ticker(sym)
            df     = ticker.earnings_dates

            if df is None or df.empty:
                continue

            df.index = df.index.tz_convert("UTC")
            mask = df.index.strftime("%Y-%m-%d") == yesterday

            if not mask.any():
                continue

            row = df[mask].iloc[0]
            eps_est    = row.get("EPS Estimate")
            eps_actual = row.get("Reported EPS")
            surprise   = row.get("Surprise(%)")

            results.append({
                "symbol":     sym,
                "date":       yesterday,
                "eps_est":    float(eps_est)    if eps_est    is not None else None,
                "eps_actual": float(eps_actual) if eps_actual is not None else None,
                "surprise":   float(surprise)   if surprise   is not None else None,
            })
            logger.info("실적 발표 감지: %s", sym)

        except Exception as e:
            logger.debug("%s 실적 조회 실패: %s", sym, e)

    return results
