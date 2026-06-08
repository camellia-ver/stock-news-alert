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
├── config.py               # .env에서 설정값 로드
├── logs/                   
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
│   └── html_utils.py
│   └── logger.py
│   └── symbol_map.py
│   └── message_formatter.py
├── gui_config.py           # GUI 설정 편집기 (선택 실행)
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

## 🖥️ GUI 설정 편집기

`config.py` 파일의 설정값을 코드 편집 없이 **GUI 앱**으로 간편하게 수정할 수 있습니다.

### 실행 방법

```bash
python gui_config.py
```

### 주요 기능

| 기능 | 설명 |
|------|------|
| 종목 관리 | 모니터링할 주식 종목 추가 / 삭제 |
| 임계값 설정 | 알림을 트리거할 가격 변동률(%) 조정 |
| 설정 저장 | 변경 사항을 `config.py`에 즉시 반영 |

---

## 🛠️ 기술 스택

| 분류 | 사용 기술 |
|------|-----------|
| 언어 | Python 3.10+ |
| 주가 조회 | [Alpha Vantage](https://www.alphavantage.co/) / [pykrx](https://github.com/sharebook-kr/pykrx) |
| 뉴스 수집 | [NewsAPI](https://newsapi.org/) / [Naver News API](https://developers.naver.com/docs/serviceapi/search/news/news.md) |
| 알림 전송 | Discord |
| GUI | tkinter (Python 표준 라이브러리) |

---

## 📬 메시지 예시

```
📊 삼성전자
- 날짜: 2026-05-30
- 변동률: -1.45%

📰 주요 뉴스
1. [제목]
   - 링크: ...
   - 설명: ...

2. [제목]
   - 링크: ...
```