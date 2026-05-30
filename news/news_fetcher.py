# news_fetcher.py
import time
import re
from datetime import datetime
from typing import Optional

from email.utils import parsedate_to_datetime
import requests
from newsapi import NewsApiClient

from settings import NEWS_API_KEY, NAVER_APPLICATION_CLIENT_ID, NAVER_APPLICATION_CLIENT_SECRET
from stock.price_checker import PriceChecker
from utils.enums import Market
from utils.logger import get_logger
from utils.html_utils import strip_html

logger = get_logger(__name__)

class NewsFetcher:
    def __init__(self, price_checker: Optional[PriceChecker] = None) -> None:
        self._news_api_key = NEWS_API_KEY
        self._naver_client_id = NAVER_APPLICATION_CLIENT_ID
        self._naver_client_secret = NAVER_APPLICATION_CLIENT_SECRET
        self._price_checker = price_checker or PriceChecker()

    def _fetch_news_from_newsapi(self) -> dict:
        '''NewsApi를 사용하여 뉴스 수집'''
        stock = self._price_checker.is_above_volatility_threshold(Market.US)
        newsapi = NewsApiClient(api_key=self._news_api_key)
        results: dict[str, list] = {}
        
        for key, item in stock.items():
            if not item:
                logger.info('Skipping %s: volatility threshold', key)
                continue

            try:
                top_headlines = newsapi.get_top_headlines(q=key,
                                                        category='business',
                                                        language='en',
                                                        country='us')
                    
                if top_headlines['status'] != 'ok':
                    logger.warning('API error for %s: %s', key, top_headlines.get('message'))
                    continue
                    
                articles = top_headlines.get("articles", [])
                results[key] = {
                     "meta": {
                        "date": item["date"],
                        "rate": item["rate"],
                    },
                    "articles": [
                        {
                            "title": a.get("title"),
                            "url": a.get("url"),
                            "source": a.get("source", {}).get("name"),
                            "published": datetime.fromisoformat(
                                a["publishedAt"].replace("Z", "+00:00")
                            ).date().isoformat() if a.get("publishedAt") else None,
                            "description": a.get("description", "설명 없음"),
                        }
                        for a in articles
                    ]
                }
                
                logger.debug('Fetched %d articles for %s', len(results[key]), key)
                time.sleep(0.5)   
            except Exception as e:
                logger.error('Failed to fetch news for %s: %s', key, e)
                continue

        return results
    
    def _parse_date(self, pub_date: str | None) -> str | None:
        if not pub_date:
            return None
        
        try:
            return parsedate_to_datetime(pub_date).date().isoformat()
        except Exception:
            return None

    def _fetch_news_from_naver(self):
        '''Naver 검색 Api를 사용하여 뉴스 수집'''
        results: dict[str, list] = {}
        stock = self._price_checker.is_above_volatility_threshold(Market.KRX)

        url = 'https://openapi.naver.com/v1/search/news.json'
        headers = {
            'X-Naver-Client-Id': self._naver_client_id,
            'X-Naver-Client-Secret': self._naver_client_secret
        }

        for key, item in stock.items():
            if not item:
                logger.info('Skipping %s: volatility threshold', key)
                continue

            params = {
                'query': key,
                'display': 10,
                'start': 1,
                'sort': 'sim'
            }

            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                json_data = response.json()
            except requests.RequestException as e:
                logger.warning('Failed to fetch news for %s: %s', key, e)
                results[key] = []
                continue

            results[key] = {
                "meta": {
                    "date": item["date"],
                    "rate": item["rate"],
                },
                "articles":[ 
                {
                    'title': strip_html(article.get('title','')),
                    'url': article.get('originallink'),
                    'source': None,
                    'published': self._parse_date(article.get('pubDate')),
                    'description': strip_html(article.get('description', ''))
                }
                for article in json_data.get('items', [])
                ]
            }
            logger.debug('Fetched %d articles for %s', len(results[key]), key)
            time.sleep(0.5)   
        
        return results

    def get_news(self) -> dict:
        '''수집한 뉴스들을 하나로 합쳐서 반환'''
        newsapi_result = self._fetch_news_from_newsapi()
        naver_result = self._fetch_news_from_naver()
        
        return {**newsapi_result, **naver_result}