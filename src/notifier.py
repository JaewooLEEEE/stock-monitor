import os
import json
import time
import logging

import requests

logger = logging.getLogger(__name__)

KAKAO_API_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
MSG_LIMIT     = 850


def _send_kakao(text: str) -> bool:
    token = os.environ.get("KAKAO_ACCESS_TOKEN", "")
    if not token:
        logger.warning("KAKAO_ACCESS_TOKEN 미설정")
        return False

    payload = json.dumps(
        {"object_type": "text", "text": text, "link": {}},
        ensure_ascii=False,
    )
    try:
        resp = requests.post(
            KAKAO_API_URL,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            data={"template_object": payload},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("result_code") == 0:
            logger.info("카카오 전송 성공")
            return True
        logger.warning("카카오 응답 오류: %s", result)
    except requests.RequestException as e:
        logger.error("카카오 전송 실패: %s", e)
    return False


def send_briefing(header: str, briefing: str):
    """헤더 + 브리핑을 850자 단위로 분할 전송."""
    full_text = f"{header}\n\n{briefing}"

    if len(full_text) <= MSG_LIMIT:
        _send_kakao(full_text)
        return

    lines  = full_text.split("\n")
    parts  = []
    chunk  = ""

    for line in lines:
        candidate = (chunk + "\n" + line).lstrip("\n")
        if len(candidate) > MSG_LIMIT:
            if chunk:
                parts.append(chunk)
            chunk = line
        else:
            chunk = candidate
    if chunk:
        parts.append(chunk)

    total = len(parts)
    for i, p in enumerate(parts, 1):
        prefix = f"({i}/{total}) " if total > 1 else ""
        _send_kakao(prefix + p)
        if i < total:
            time.sleep(0.8)
