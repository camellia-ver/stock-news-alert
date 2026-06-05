import requests
import os
from settings import DISCORD_WEBHOOK_URL
from utils.message_formatter import format_message

class Sender:
    def __init__(self):
        self.url = DISCORD_WEBHOOK_URL

    def sending_discord(self, data):
        if not data:
            return
        
        url = self.url

        all_message = '\n\n'.join(
            format_message(symbol, data)
            for symbol, data in data.items()
        )

        response = requests.post(
            url,
            json={'content': all_message}
        )