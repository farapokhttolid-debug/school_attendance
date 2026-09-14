import sqlite3
from core.database import get_db_connection
from core.logger import get_logger

logger = get_logger(__name__)


def init_db():
    """ساخت جدول‌های اصلی پروژه"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # جدول پرسنل
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_code TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone1 TEXT,
            phone2 TEXT,
            telegram_chat_id TEXT,
            bale_chat_id TEXT,
            position TEXT,
            is_active INTEGER DEFAULT 1,
            signature_path TEXT,
            created_at TEXT
        )
    ''')

    # جدول حضور و غیاب
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            entry_time TEXT,
            exit_time TEXT,
            status TEXT DEFAULT 'present',
            note TEXT,
            created_at TEXT,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id)
        )
    ''')

    # جدول کاربران سیستم
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            personnel_id INTEGER,
            is_admin INTEGER DEFAULT 0,
            is_super_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id)
        )
    ''')

    # جدول تنظیمات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("✅ جدول‌های دیتابیس ساخته شدند")