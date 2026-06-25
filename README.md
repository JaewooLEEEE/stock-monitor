# stock-monitor

미국 증시 마감 직후 자동으로 데이터를 수집하고 Claude AI가 서술형으로 분석한 브리핑을 카카오톡으로 받는 시스템입니다.

---

## 기능

- 미국 3대 지수 (S&P500, 나스닥, 다우) + VIX 수집
- 매크로 지표 (미 10년물 금리, 달러인덱스, 달러/원, 달러/엔, 금, WTI원유)
- 반도체 섹터 (NVDA, AMD, INTC, TSM, ASML, AMAT, MU, QCOM)
- 빅테크 (AAPL, MSFT, AMZN, META, GOOGL)
- 전날 실적 발표 종목 자동 감지 (EPS 예상 대비 실제, 서프라이즈%)
- 글로벌 뉴스 수집 (NEWSAPI_KEY 있으면 NewsAPI, 없으면 yfinance 내장 뉴스)
- Claude AI로 숫자 나열이 아닌 **왜 그렇게 움직였는지** 서술형 브리핑 생성
- 카카오톡 분할 전송 (850자 초과 시 자동 분할)
- 카카오 Refresh Token 자동 갱신 (최초 1회 등록 후 무기한 자동 운용)
- GitHub Actions artifact로 로그 7일 보관

---

## 실행 스케줄

| 시간 | 설명 |
|------|------|
| UTC 21:30 (월~금) | 미국 정규장 마감(EST 16:00) 30분 후 실행 |
| KST 06:30 (화~토) | 카카오톡 수신 기준 (GitHub Actions 지연 감안 시 ~07:30) |

> EST(겨울) 기준 마감 30분 후. EDT(여름)에는 마감 90분 후 실행되므로 더 일찍 수신됩니다.

---

## 브리핑 형식

숫자 나열 없이 아래 5개 섹션을 서술형으로 작성합니다.

1. **전날 미장 흐름** — 어떻게 움직였고 왜 그랬는지 (장중 반전이 있었다면 이유 포함)
2. **매크로** — 금리/환율/원자재 중 시장에 영향 준 것과 이유
3. **반도체/테크** — 섹터 흐름과 주목 종목, 왜 그 종목이 튀었는지
4. **실적** — 발표가 있는 경우만, 예상 대비 어땠고 시장 반응은
5. **오늘 국내 시장** — 코스피/코스닥 전망

---

## 사전 준비

### 1. GitHub 레포 생성

```bash
git init
git remote add origin https://github.com/<your-id>/stock-monitor.git
git add .
git commit -m "init"
git push -u origin main
```

### 2. Anthropic API 키 발급

1. [Anthropic Console](https://console.anthropic.com) 접속
2. **API Keys** → **Create Key**
3. 키 복사

### 3. 카카오 토큰 발급

apt-monitor와 동일한 카카오 앱/토큰을 재사용할 수 있습니다.
신규 발급이 필요한 경우 [apt-monitor README](https://github.com/JaewooLEEEE/apt-monitor#4-%EC%B9%B4%EC%B9%B4%EC%98%A4-%ED%86%A0%ED%81%B0-%EB%B0%9C%EA%B8%89-%EC%B5%9C%EC%B4%88-1%ED%9A%8C) 의 4번 항목을 참고하세요.

### 4. GitHub Secrets 등록

레포 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 이름           | 값                              | 필수 |
|----------------------|---------------------------------|------|
| `ANTHROPIC_API_KEY`  | Anthropic API 키                | ✅   |
| `KAKAO_REST_API_KEY` | 카카오 앱의 REST API 키          | ✅   |
| `KAKAO_REFRESH_TOKEN`| 카카오 refresh_token             | ✅   |
| `GH_PAT`             | repo 권한의 GitHub Personal Access Token | ✅ |
| `KAKAO_CLIENT_SECRET`| 카카오 앱의 Client Secret (있는 경우) | ➖ |
| `NEWSAPI_KEY`        | [NewsAPI](https://newsapi.org) 키 (없으면 yfinance 뉴스 사용) | ➖ |

> **apt-monitor와 같은 카카오 계정을 쓴다면** Secrets 값을 그대로 복사하면 됩니다.
> apt-monitor의 `copy_secrets.yml` 워크플로를 수동 실행하면 자동으로 복사됩니다.

### 5. GitHub Actions 권한 설정

레포 → **Settings** → **Actions** → **General** → **Workflow permissions**
→ **Read and write permissions** 선택 후 저장

---

## 로컬 실행

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# .env 파일에 각 키 값 입력

python main.py
```

---

## 수동 실행

레포 → **Actions** → **Daily Stock Briefing** → **Run workflow**

---

## 파일 구조

```
stock-monitor/
├── main.py                        # 진입점
├── requirements.txt
├── .env.example                   # 환경변수 템플릿
├── src/
│   ├── market_data.py             # yfinance로 지수/매크로/섹터 데이터 수집
│   ├── earnings.py                # 전날 실적 발표 종목 감지
│   ├── news_fetcher.py            # 뉴스 수집 (NewsAPI or yfinance)
│   ├── analyzer.py                # Claude AI 서술형 브리핑 생성
│   ├── kakao_auth.py              # 카카오 토큰 갱신
│   └── notifier.py                # 카카오톡 분할 전송
└── .github/
    └── workflows/
        └── daily_stock.yml        # GitHub Actions 스케줄러
```

---

## 카카오 토큰 자동 갱신 흐름

apt-monitor와 동일한 방식으로 동작합니다.

```
매일 실행
  └─ KAKAO_REFRESH_TOKEN 으로 새 access_token 발급
       └─ 카카오가 새 refresh_token 도 함께 반환한 경우
            └─ .kakao_tokens.json 에 기록
                 └─ 워크플로 "Update secret" step 이
                    KAKAO_REFRESH_TOKEN Secret 을 자동 업데이트
```

---

## 주의사항

- yfinance 데이터는 실시간이 아니며 전날 종가 기준입니다.
- NewsAPI 무료 플랜은 하루 100건 제한이 있습니다. 일 1회 실행이므로 충분합니다.
- `.kakao_tokens.json` 은 워크플로 실행 후 자동 삭제됩니다.
