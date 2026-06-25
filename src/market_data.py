"""
미국 주요 지수, 매크로 지표, 반도체/테크 종목 데이터 수집.
yfinance 를 사용하므로 별도 API 키 불필요.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import yfinance as yf

logger = logging.getLogger(__name__)

INDICES = {
    "S&P500":  "^GSPC",
    "나스닥":   "^IXIC",
    "다우":     "^DJI",
    "VIX":     "^VIX",
}

MACRO = {
    "미10Y금리": "^TYX",     # ^TNX 불안정 — ^TYX(30Y 수익률)로 대체
    "달러인덱스": "DX-Y.NYB",
    "달러/원":   "KRW=X",
    "달러/엔":   "JPY=X",
    "금":        "GC=F",
    "WTI원유":  "CL=F",
}

SEMICON = {
    "NVDA":  "NVDA",
    "AMD":   "AMD",
    "INTC":  "INTC",
    "TSM":   "TSM",
    "ASML":  "ASML",
    "AMAT":  "AMAT",
    "MU":    "MU",
    "QCOM":  "QCOM",
}

TECH = {
    "AAPL":  "AAPL",
    "MSFT":  "MSFT",
    "AMZN":  "AMZN",
    "META":  "META",
    "GOOGL": "GOOGL",
}


def _fetch_group(tickers: dict[str, str]) -> dict[str, dict]:
    """티커 그룹 일괄 조회. {이름: {close, prev_close, change_pct, ...}} 반환."""
    symbols = list(tickers.values())
    names   = {v: k for k, v in tickers.items()}

    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=5)  # 주말·공휴일 대비 여유

    try:
        raw = yf.download(
            symbols,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
            group_by="ticker",
        )
    except Exception as e:
        logger.error("yfinance 다운로드 실패: %s", e)
        return {}

    results: dict[str, dict] = {}
    for sym in symbols:
        name = names[sym]
        try:
            if len(symbols) == 1:
                close_series = raw["Close"]
            else:
                close_series = raw[sym]["Close"]

            close_series = close_series.dropna()
            if len(close_series) < 2:
                continue

            close      = float(close_series.iloc[-1])
            prev_close = float(close_series.iloc[-2])
            change     = close - prev_close
            change_pct = change / prev_close * 100

            results[name] = {
                "symbol":     sym,
                "close":      close,
                "prev_close": prev_close,
                "change":     change,
                "change_pct": change_pct,
                "date":       close_series.index[-1].strftime("%Y-%m-%d"),
            }
        except Exception as e:
            logger.warning("%s 파싱 실패: %s", sym, e)

    return results


def fetch_all() -> dict:
    """전체 시장 데이터 수집. 구조: {indices, macro, semicon, tech}"""
    logger.info("시장 데이터 수집 시작")
    return {
        "indices": _fetch_group(INDICES),
        "macro":   _fetch_group(MACRO),
        "semicon": _fetch_group(SEMICON),
        "tech":    _fetch_group(TECH),
    }
