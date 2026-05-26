# news_fetcher.py
import json
import time
from typing import Optional

from newsapi import NewsApiClient

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
        newsapi = NewsApiClient(api_key=self._news_api_key)
        
        for key, item in stock.items():
            if item:
                top_headlines = newsapi.get_top_headlines(q=key,
                                                      category='business',
                                                      language='en',
                                                      country='us')
                
                if top_headlines['status'] != 'ok':
                    raise Exception(top_headlines.get('message', 'API 오류'))
                
                articles = top_headlines["articles"]

                simplified = [
                    {
                        "title": a["title"],
                        "url": a["url"],
                        "source": a["source"]["name"],          # 중첩 접근
                        "published": a["publishedAt"][:10],     # 날짜만 자르기
                        "image": a.get("urlToImage"),           # 없을 수 있는 필드
                        "description": a.get("description", "설명 없음"),
                    }
                    for a in articles
                ]

                print(simplified)  
                time.sleep(0.5)   


    def fetch_news_from_naver(self):
        '''Naver 검색 Api를 사용하여 뉴스 수집'''
        stock = self._price_checker.is_above_volatility_threshold(Market.KRX)

    def get_news(self) -> dict:
        '''수집한 뉴스들을 하나로 합쳐서 반환'''
        newsapi_result = self.fetch_news_from_newsapi()
        naver_result = self.fetch_news_from_naver()
        
        return [*newsapi_result, *naver_result]