import requests
from settings import DISCORD_WEBHOOK_URL
from utils.message_formatter import format_message
from utils.logger import get_logger
from news.summarizer import Summarizer
import time

logger = get_logger(__name__)

class Sender:
    def __init__(self):
        self.url = DISCORD_WEBHOOK_URL

    def send_discord(self, data):
        if not data:
            return
    
        formatted_messages = [
            format_message(symbol, info)
            for symbol, info in data.items()
        ]
        
        all_message = '\n\n'.join(formatted_messages)

        summarizer = Summarizer()
        try:
            insight_text = summarizer.summarizer_by_gemini(all_message)
        except Exception as e:
            logger.error(f'AI 요약 생성 실패: {e}')
            insight_text = '(AI 요약 생성에 실패했습니다)'

        if not insight_text or not insight_text.strip():
            insight_text = '(AI 요약 내용이 비어 있습니다)'

        all_message = f'🧠 AI 인사이트\n{insight_text}'

        for chunk in self._split_message(all_message):
            self._send_chuck(chunk)

    def _send_chuck(self, chuck, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.post(self.url, json={'content': chunk}, timeout=10)
            except requests.exceptions.RequestException as e:
                logger.error(f'Discord 전송 중 네트워크 오류: {e}')
                return

            if response.status_code == 204:
                logger.info(f'상태 코드: {response.status_code}')
                return
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 1)
                logger.error(f'429 Rate limit, {retry_after}초 대기 후 재시도 ({attempt + 1}/{max_retries})')
                time.sleep(retry_after)
            else:
                logger.error(f'상태 코드: {response.status_code}, 응답: {response.text}')
                return
            
        logger.error('최대 재시도 횟수 초과, 전송 실패')

    def _split_message(self, message, limit=2000):
        chunks = []

        while len(message) > limit:
            split_index = message.rfind('\n', 0, limit)

            if split_index == -1:
                split_index = limit

            chunks.append(message[:split_index])
            message = message[split_index:].lstrip('\n')
        chunks.append(message)

        return chunks