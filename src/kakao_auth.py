import os
import json
import logging

import requests

logger = logging.getLogger(__name__)

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
TOKEN_CACHE_FILE = ".kakao_tokens.json"


def refresh_kakao_token() -> str:
    refresh_token = os.environ.get("KAKAO_REFRESH_TOKEN", "")
    rest_api_key  = os.environ.get("KAKAO_REST_API_KEY", "")

    if not refresh_token or not rest_api_key:
        raise ValueError("KAKAO_REFRESH_TOKEN 또는 KAKAO_REST_API_KEY 가 설정되지 않았습니다.")

    client_secret = os.environ.get("KAKAO_CLIENT_SECRET", "")

    data: dict = {
        "grant_type":    "refresh_token",
        "client_id":     rest_api_key,
        "refresh_token": refresh_token,
    }
    if client_secret:
        data["client_secret"] = client_secret

    resp = requests.post(KAKAO_TOKEN_URL, data=data, timeout=10)
    resp.raise_for_status()
    result = resp.json()

    if "error" in result:
        raise RuntimeError(
            f"카카오 토큰 갱신 실패: {result.get('error_description', result['error'])}"
        )

    new_access_token  = result["access_token"]
    new_refresh_token = result.get("refresh_token")

    cache: dict = {"access_token": new_access_token}
    if new_refresh_token:
        cache["refresh_token"] = new_refresh_token
        logger.info("카카오 refresh_token 도 갱신됨 — %s 에 기록", TOKEN_CACHE_FILE)
    else:
        logger.info("카카오 access_token 갱신 완료 (refresh_token 유지)")

    with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    return new_access_token
