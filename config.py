# config.py
STOCK_TICKERS = {
    'KRX': {
        "005930": "삼성전자",
        "000660": "SK하이닉스",
        "035420": "NAVER",
    },
    'US': {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "NVDA": "NVIDIA",
        "TSLA": "Tesla",
    },
} # 모니터링 종목

ALERT_THRESHOLD = 10  # 변동률 임계값 (%)