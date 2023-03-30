import base64
import datetime
import json
import os
import re
import time
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
            bot_id='',
            chat_id='',
            min_severity=70,
        )

        if config is not None:
            lconfig = config.get(self.id, {})
            self._bot_id = lconfig.get('bot_id', None)
            self._chat_id = lconfig.get('chat_id', None)
            self._min_severity = lconfig.get('min_severity', self._min_severity)
            del lconfig

            if self._bot_id.strip() == '':
                self._bot_id = None

            if self._bot_id is not None and self._bot_id[0:3].lower() != 'bot':
                self._bot_id = f'bot{self._bot_id}'

    def send_alert(self, match: str, indexing_date: datetime.datetime, rule: str,
                   filtered_file: str, content: str, severity: int, image_file: Path):

        if 0 <= severity < self._min_severity:
            return

        # https://apps.timwhitlock.info/emoji/tables/unicode
        requests.packages.urllib3.disable_warnings()

        image_id = -1
        try:
            pic = Telegram.adjust_picture(image_file)
            if pic is not None:
                with(open(pic, 'rb')) as f:
                    files = {'photo': f}

                    r1 = requests.post(
                        f"https://api.telegram.org/{self._bot_id}/sendPhoto?chat_id={self._chat_id}",
                        verify=False,
                        timeout=30,
                        files=files
                    )
                    if r1.status_code == 200:
                        data = r1.json()
                        if data is not None:
                            image_id = data.get('result', {}).get('message_id', -1)
                    elif r1.status_code == 502:
                        time.sleep(1)
                        r1 = requests.post(
                            f"https://api.telegram.org/{self._bot_id}/sendPhoto?chat_id={self._chat_id}",
                            verify=False,
                            timeout=30,
                            files=files
                        )
                        if r1.status_code == 200:
                            data = r1.json()
                            if data is not None:
                                image_id = data.get('result', {}).get('message_id', -1)
                    else:
                        print(' ')
                        print(pic)
                        print(match)
                        print(r1.text)
        except Exception as e:
            print(e)
            pass

        text = f'\U0001F6A8 ALERT \U0001F6A8 \n'
        text += f'New credential found by rule {rule}\n\n'
        text += content
        text += '\n'

        header = {'content-type': 'application/json'}
        data = {
            'chat_id': self._chat_id,
            'text': text
        }

        if image_id != -1:
            data.update(dict(reply_to_message_id=image_id))

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

    def is_enabled(self) -> bool:
        if self._bot_id is None or self._chat_id is None:
            return False

        return True

    @staticmethod
    def adjust_picture(image_file: Path) -> Optional[Path]:
        '''The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20.'''
        from PIL import Image, ImageDraw
        from filecrawler.util.tools import Tools
        from filecrawler.config import Configuration
        from filecrawler.libs.logger import Logger

        if not image_file.exists():
            return None

        try:
            changed = False
            with Image.open(image_file) as img:
                color = img.getpixel((3, 3))
                if img.size[0] > 10000 or img.size[1] > 10000:
                    l = float(img.size[0])
                    if img.size[1] > l:
                        l = float(img.size[1])
                    r = 10000.0 / l
                    ns = (int(img.size[0] * r), int(img.size[1] * r))
                    if Configuration.verbose >= 1:
                        Logger.pl('{?} {GR}Resizing image {O}%s{W} from %s:%s to %s:%s\n' %
                                  (image_file, img.size[0], img.size[1], ns[0], ns[1]))
                    img = img.resize(ns)

                    changed = True

                f_size = (float(img.size[0]), float(img.size[1]))
                min_w = f_size[1] * 0.8
                if f_size[0] < min_w:
                    (w, h) = img.size
                    w = int(min_w) + 1

                    if Configuration.verbose >= 1:
                        Logger.pl('{?} {GR}Resizing image {O}%s{W} from %s:%s to %s:%s\n' %
                                  (image_file, img.size[0], img.size[1], w, h))

                    changed = True
                    n_img = Image.new("RGB", (w, h), color)
                    n_img.paste(img, (0, 0))
                    img = n_img.copy()

                #ratio = f_size[1] / f_size[0] if f_size[0] > f_size[1] else f_size[0] / f_size[1]
                #if ratio < 0.8:
                #    (w, h) = img.size
                #    if w > h:
                #        h = int(w * 0.85)
                #    else:
                #        w = int(h * 0.85)

                if changed:
                    nf = os.path.join(image_file.parent, image_file.name.replace(image_file.suffix, '_telegram.png'))
                    img.save(nf, format='png', subsampling=0, quality=100)
                    image_file = Path(nf)

        except Exception as e:
            Tools.print_error(e)

        return image_file