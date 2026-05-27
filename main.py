from news.news_fetcher import NewsFetcher
from utils.logger import setup_logging

setup_logging()
print(NewsFetcher()._fetch_news_from_naver())