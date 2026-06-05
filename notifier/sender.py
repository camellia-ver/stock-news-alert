import requests
from settings import DISCORD_WEBHOOK_URL
from utils.message_formatter import format_message
from utils.logger import get_logger

logger = get_logger(__name__)

class Sender:
    def __init__(self):
        self.url = DISCORD_WEBHOOK_URL

    def sending_discord(self, data):
        if not data:
            return
    
        all_message = '\n\n'.join(
            format_message(symbol, info)
            for symbol, info in data.items()
        )

        for chunk in self._split_message(all_message):
            response = requests.post(
                self.url,
                json={'content': chunk}
            )
            if response.status_code == 204:
                logger.info(f'상태 코드: {response.status_code}')
            else:
                logger.error(f'상태 코드: {response.status_code}')

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