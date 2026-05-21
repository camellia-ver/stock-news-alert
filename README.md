# 📈 stock-news-alert

> 특정 주식 가격 변동에 따라 해당 주식 관련 뉴스를 자동으로 전송하는 알림 서비스

---

## 📌 프로젝트 소개

`stock-news-alert`는 사용자가 지정한 주식 종목의 가격 변동률이 임계값을 초과할 경우, 관련 최신 뉴스를 자동으로 수집하여 알림으로 전송하는 Python 기반 자동화 프로그램입니다.

---

## 🗂️ 프로젝트 구조

```
stock-news-alert/
├── main.py                  # 메인 실행 파일
├── config.py               # .env에서 설정값 로드
├── stock/
│   ├── __init__.py
│   └── price_checker.py    # 주식 가격 조회 및 변동률 계산
├── news/
│   ├── __init__.py
│   └── news_fetcher.py     # 주식 관련 뉴스 수집
├── notifier/
│   ├── __init__.py
│   └── sender.py           # 알림 전송
├── utils
│   └── enums.py
├── .env                    # API 키 (gitignore 처리)
├── .env.example            # .env 템플릿 (공유용)
├── config.py               # 설정값
├── settings.py             # .env 로드
├── requirements.txt
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
| 주가 조회 | [yfinance](https://ranaroussi.github.io/yfinance/) / [pykrx](https://github.com/sharebook-kr/pykrx) |
| 뉴스 수집 | [NewsAPI](https://newsapi.org/) / [Naver News API](https://developers.naver.com/docs/serviceapi/search/news/news.md)|
| 알림 전송 | Discord |

---

## 📬 메시지 예시
```
주식명 🚨 주식가격 급변!

📅 날짜 YYYY-MM-DD

📰 뉴스
    1. 뉴스1
    2. 뉴스2
    3. 뉴스3    
```