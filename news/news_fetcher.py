from typing import Optional
from settings import NEWS_API_KEY, NAVER_APPLICATION_CLIENT_ID, NAVER_APPLICATION_CLIENT_SECRET
from stock.price_checker import PriceChecker

class NewsFetcher:
    def __init__(self, price_checker: Optional[PriceChecker] = None) -> None:
        self._news_api_key = NEWS_API_KEY
        self._naver_client_id = NAVER_APPLICATION_CLIENT_ID
        self._naver_client_secret = NAVER_APPLICATION_CLIENT_SECRET
        self._price_checker = price_checker or PriceChecker()
