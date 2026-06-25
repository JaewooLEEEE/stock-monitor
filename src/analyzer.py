"""Claude AI로 수집 데이터를 한국어 브리핑으로 요약."""
from __future__ import annotations

import os
import json
import logging

import anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"


def _fmt_market(data: dict) -> str:
    lines = []
    for group_name, group in [("미국 지수", data["indices"]),
                               ("매크로",   data["macro"]),
                               ("반도체",   data["semicon"]),
                               ("빅테크",   data["tech"])]:
        if not group:
            continue
        lines.append(f"[{group_name}]")
        for name, d in group.items():
            sign  = "+" if d["change_pct"] >= 0 else ""
            close = d["close"]
            pct   = d["change_pct"]
            if name in ("달러/원", "달러/엔", "미10Y금리", "달러인덱스"):
                lines.append(f"  {name}: {close:.3f} ({sign}{pct:.2f}%)")
            elif name in ("금", "WTI원유"):
                lines.append(f"  {name}: ${close:.1f} ({sign}{pct:.2f}%)")
            else:
                lines.append(f"  {name}: {close:,.2f} ({sign}{pct:.2f}%)")
    return "\n".join(lines)


def _fmt_earnings(earnings: list[dict]) -> str:
    if not earnings:
        return "어제 주요 실적 발표 없음"
    lines = ["[어제 실적 발표]"]
    for e in earnings:
        sym  = e["symbol"]
        act  = e["eps_actual"]
        est  = e["eps_est"]
        surp = e["surprise"]
        act_str  = f"${act:.2f}" if act  is not None else "N/A"
        est_str  = f"${est:.2f}" if est  is not None else "N/A"
        surp_str = f"{surp:+.1f}%" if surp is not None else ""
        lines.append(f"  {sym}: EPS {act_str} (예상 {est_str}) {surp_str}")
    return "\n".join(lines)


def _fmt_news(news: dict) -> str:
    lines = []
    for section, items in news.items():
        label = {"market": "시장 뉴스", "macro": "매크로 뉴스", "semicon": "반도체/AI 뉴스"}.get(section, section)
        if items:
            lines.append(f"[{label}]")
            for item in items:
                lines.append(f"  - {item['title']} ({item['source']})")
    return "\n".join(lines)


def generate_briefing(market_data: dict, earnings: list[dict], news: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY 미설정 — 원시 데이터만 반환")
        return f"{_fmt_market(market_data)}\n\n{_fmt_earnings(earnings)}"

    raw_data = f"""
{_fmt_market(market_data)}

{_fmt_earnings(earnings)}

{_fmt_news(news)}
""".strip()

    prompt = f"""다음은 어제 미국 증시 마감 후 수집한 데이터입니다.

{raw_data}

위 데이터를 바탕으로 한국 투자자를 위한 아침 증시 브리핑을 작성해주세요.

형식:
1. 전날 미장 핵심 요약 (3줄 이내)
2. 주요 매크로 포인트 (금리/환율/원자재 중 주목할 것)
3. 반도체/테크 동향 (섹터 흐름 + 주목 종목)
4. 국내 시장 전망 (코스피/코스닥에 미칠 영향)
5. 실적 발표 요약 (있는 경우)
6. 오늘 주목할 포인트

간결하고 핵심만, 총 500자 이내로 작성해주세요. 불필요한 인사말 없이 바로 시작하세요."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg    = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        briefing = msg.content[0].text.strip()
        logger.info("Claude 브리핑 생성 완료 (%d자)", len(briefing))
        return briefing
    except Exception as e:
        logger.error("Claude API 호출 실패: %s", e)
        return raw_data
