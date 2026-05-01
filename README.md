# 📈 stock-news-alert

> 특정 주식 가격 변동에 따라 해당 주식 관련 뉴스를 자동으로 전송하는 알림 서비스

---

## 📌 프로젝트 소개

`stock-news-alert`는 사용자가 지정한 주식 종목의 가격 변동률이 임계값을 초과할 경우, 관련 최신 뉴스를 자동으로 수집하여 알림으로 전송하는 Python 기반 자동화 프로그램입니다.

---

## 🗂️ 프로젝트 구조

```
stock-news-alert/
├── main.py                 # 메인 실행 파일
├── config.py               # 설정값 관리 (종목, 임계값 등)
├── stock/
│   ├── __init__.py
│   └── price_checker.py    # 주식 가격 조회 및 변동률 계산
├── news/
│   ├── __init__.py
│   └── news_fetcher.py     # 주식 관련 뉴스 수집
├── notifier/
│   ├── __init__.py
│   └── sender.py           # 알림 전송 
├── .env                    # 환경변수 (API Key 등, git 제외)
├── .env.example            # 환경변수 예시 파일
├── requirements.txt        # 의존성 패키지 목록
└── README.md
```

---

## ⚙️ 동작 흐름

```
1. 주기적으로 지정 종목의 현재 주가를 조회
2. 전일 대비 변동률이 임계값(예: ±5%) 초과 여부 확인
3. 임계값 초과 시 해당 종목 관련 최신 뉴스 수집
4. Discord로 뉴스 알림 전송
```

---

## 🛠️ 기술 스택

| 분류 | 사용 기술 |
|------|-----------|
| 언어 | Python 3.10+ |
| 주가 조회 | [Alpha Vantage API](https://www.alphavantage.co/) |
| 뉴스 수집 | [NewsAPI](https://newsapi.org/) |
| 알림 전송 | Twilio(SMS) / Slack Webhook / SMTP |
| 스케줄링 | `schedule` 라이브러리 |
| 환경변수 | `python-dotenv` |

---

## 🚀 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/stock-news-alert.git
cd stock-news-alert
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 값을 입력합니다.

```bash
cp .env.example .env
```

```env
# .env.example

STOCK_API_KEY=your_stock_api_key
NEWS_API_KEY=your_news_api_key
```

### 4. 종목 및 임계값 설정

`config.py`에서 모니터링할 종목과 변동률 임계값을 설정합니다.

```python
# config.py
STOCK_SYMBOLS = ["TSLA", "AAPL", "005930.KS"]  # 모니터링 종목
ALERT_THRESHOLD = 5  # 변동률 임계값 (%)
CHECK_INTERVAL = 60  # 조회 주기 (초)
```

### 5. 실행

```bash
python main.py
```

---

## 📦 requirements.txt 예시

```
requests
schedule
python-dotenv
newsapi-python
```
