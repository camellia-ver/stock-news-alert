from newsapi import NewsApiClient
from typing import Optional
from settings import NEWS_API_KEY, NAVER_APPLICATION_CLIENT_ID, NAVER_APPLICATION_CLIENT_SECRET
from stock.price_checker import PriceChecker
from utils.enums import Market

class NewsFetcher:
    def __init__(self, price_checker: Optional[PriceChecker] = None) -> None:
        self._news_api_key = NEWS_API_KEY
        self._naver_client_id = NAVER_APPLICATION_CLIENT_ID
        self._naver_client_secret = NAVER_APPLICATION_CLIENT_SECRET
        self._price_checker = price_checker or PriceChecker()

    def fetch_news_from_newsapi(self) -> dict:
        '''NewsApi를 사용하여 뉴스 수집'''
        stock = self._price_checker.is_above_volatility_threshold(Market.US)
        # newsapi = NewsApiClient(api_key=self._news_api_key)
        # top_headlines = newsapi.get_top_headlines(q=)

    def fetch_news_from_naver(self):
        '''Naver 검색 Api를 사용하여 뉴스 수집'''
        stock = self._price_checker.is_above_volatility_threshold(Market.KRX)

    def get_news(self) -> dict:
        '''수집한 뉴스들을 하나로 합쳐서 반환'''
        newsapi_result = self.fetch_news_from_newsapi()
        naver_result = self.fetch_news_from_naver()
        
        return [*newsapi_result, *naver_result]