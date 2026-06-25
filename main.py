import os
import logging
from datetime import datetime

from src.kakao_auth  import refresh_kakao_token
from src.market_data import fetch_all
from src.earnings    import fetch_yesterday_earnings
from src.news_fetcher import fetch_news
from src.analyzer    import generate_briefing
from src.notifier    import send_briefing

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("stock_monitor.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== stock-monitor 시작 ===")

    # 카카오 토큰 갱신
    access_token = refresh_kakao_token()
    os.environ["KAKAO_ACCESS_TOKEN"] = access_token

    # 데이터 수집
    market_data = fetch_all()
    earnings    = fetch_yesterday_earnings()
    news        = fetch_news()

    logger.info("실적 발표 종목: %d개", len(earnings))

    # Claude 브리핑 생성
    briefing = generate_briefing(market_data, earnings, news)

    # 카카오톡 전송
    today  = datetime.now().strftime("%m/%d(%a)")
    header = f"[미장 브리핑] {today}"
    send_briefing(header, briefing)

    logger.info("=== 완료 ===")


if __name__ == "__main__":
    main()
