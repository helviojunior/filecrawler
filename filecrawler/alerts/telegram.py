import base64
import datetime
import json
import re
from pathlib import Path
from typing import Optional

import requests

from filecrawler.alertbase import AlertBase


class Telegram(AlertBase):
    _bot_id = None
    _chat_id = None

    def __init__(self, config: Optional[dict] = None):
        super().__init__('telegram', 'Telegram Alerter')

        self._config_sample = dict(
            bot_id='telegram_bot_id',
            chat_id='telegram_chat_id',
        )

        if config is not None:
            lconfig = config.get(self.id, {})
            self._bot_id = lconfig.get('bot_id', None)
            self._chat_id = lconfig.get('chat_id', None)
            del lconfig

            if self._bot_id is not None and self._bot_id[0:3].lower() != 'bot':
                self._bot_id = f'bot{self._bot_id}'

    def send_alert(self, match: str, indexing_date: datetime.datetime, rule: str, filtered_file: str, content: str, image_file: Path):

        requests.packages.urllib3.disable_warnings()

        text = f'New credential found by rule {rule}\n'
        text += f'Math: {match}\n\n'
        text += content

        header = {'content-type': 'application/json'}
        data = {
            'chat_id': self._chat_id,
            'text': text
        }

        try:
            requests.post(
                f"https://api.telegram.org/{self._bot_id}/sendMessage",
                verify=False,
                timeout=30,
                headers=header,
                data=json.dumps(data)
            )
        except:
            pass

        try:
            if image_file.exists():
                with(open(image_file, 'rb')) as f:
                    files = {'photo': f}

                    requests.post(
                        f"https://api.telegram.org/{self._bot_id}/sendPhoto?chat_id={self._chat_id}",
                        verify=False,
                        timeout=30,
                        files=files
                    )
        except Exception as e:
            print(e)
            pass

    def is_enabled(self) -> bool:
        if self._bot_id is None or self._chat_id is None:
            return False

        return True
