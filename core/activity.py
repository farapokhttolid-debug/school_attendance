from datetime import datetime
from flask import session
from core.database import get_db_connection
from core.logger import get_logger

logger = get_logger(__name__)


def get_today_jalali():
    try:
        import jdatetime
        return jdatetime.date.today().strftime('%Y/%m/%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')


def get_now_time():
    return datetime.now().strftime('%H:%M:%S')


def log_activity(action, target_type=None, target_id=None, details=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        school_id = session.get('school_id')
        username = session.get('username', 'system')

        cursor.execute('''
            INSERT INTO activity_log
            (school_id, username, action, target_type, target_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            school_id,
            username,
            action,
            target_type,
            target_id,
            details,
            f"{get_today_jalali()} {get_now_time()}"
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطا در ثبت لاگ: {e}")