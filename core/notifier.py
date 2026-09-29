import os
import requests
from core.logger import get_logger

logger = get_logger(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
BALE_TOKEN = os.environ.get('BALE_BOT_TOKEN', '')


def send_telegram(chat_id, message):
    if not TELEGRAM_TOKEN:
        return False, 'توکن تلگرام تنظیم نشده'
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        res = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)
        data = res.json()
        if data.get('ok'):
            return True, 'ارسال شد'
        return False, data.get('description', 'خطای ناشناخته')
    except Exception as e:
        logger.error(f"خطا در ارسال تلگرام: {e}")
        return False, str(e)


def send_bale(chat_id, message):
    if not BALE_TOKEN:
        return False, 'توکن بله تنظیم نشده'
    try:
        url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
        res = requests.post(url, json={
            'chat_id': chat_id,
            'text': message
        }, timeout=10)
        data = res.json()
        if data.get('ok'):
            return True, 'ارسال شد'
        return False, data.get('description', 'خطای ناشناخته')
    except Exception as e:
        logger.error(f"خطا در ارسال بله: {e}")
        return False, str(e)


def send_to_parent(platform, chat_id, message):
    if platform == 'telegram':
        return send_telegram(chat_id, message)
    elif platform == 'bale':
        return send_bale(chat_id, message)
    return False, 'پلتفرم نامعتبر'