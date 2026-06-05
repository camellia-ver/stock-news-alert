from news.news_fetcher import NewsFetcher
from utils.logger import setup_logging, get_logger
from notifier import sender

logger = get_logger(__name__)

if __name__ == '__main__':
    setup_logging()

    try:
        news = NewsFetcher().get_news()
        logger.info(f"뉴스 {len(news)}개 수집 완료")
        discord_sender = sender.Sender()
        discord_sender.sending_discord(news)
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        raise