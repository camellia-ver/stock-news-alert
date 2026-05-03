# 📈 stock-news-alert

> 특정 주식 가격 변동에 따라 해당 주식 관련 뉴스를 자동으로 전송하는 알림 서비스

---

## 📌 프로젝트 소개

`stock-news-alert`는 사용자가 지정한 주식 종목의 가격 변동률이 임계값을 초과할 경우, 관련 최신 뉴스를 자동으로 수집하여 알림으로 전송하는 Python 기반 자동화 프로그램입니다.

---

## 🗂️ 프로젝트 구조

```
stock-news-alert/
├── .github/
│   └── workflows/
│       └── schedule.yml          # GitHub Actions 자동 실행 스케줄
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
├── requirements.txt        # 의존성 패키지 목록
├── README.md
└── .gitignore
```

---

## ⚙️ 동작 흐름

```
1. 장이 열리는 날 아침 지정 종목의 하루전과 이틀전의 종가를 조회
2. 조회한 종가의 변동률이 임계값(예: ±5%) 초과 여부 확인
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
| 알림 전송 | Discord |

---

## 🔒 GitHub Secrets 설정

| Secret 이름 | 설명 |
|------|-----------|
| STOCK_API_KEY | Alpha Vantage API Key |
| NEWS_API_KEY | NewsAPI Key |
| DISCORD_WEBHOOK_URL | Discord 채널 웹훅 URL |
