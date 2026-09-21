import sqlite3
from core.database import get_db_connection
from core.logger import get_logger

logger = get_logger(__name__)


def init_db():
    """ساخت جدول‌های اصلی پروژه"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # ========== جدول مدارس ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            address TEXT,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
    ''')

    # ========== جدول پرسنل (کاربران سیستم) ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            personnel_code TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone1 TEXT,
            phone2 TEXT,
            position TEXT,
            is_active INTEGER DEFAULT 1,
            signature_path TEXT,
            created_at TEXT,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
    ''')

    # ========== جدول کاربران ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            personnel_id INTEGER,
            is_super_admin INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            UNIQUE(school_id, username),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (personnel_id) REFERENCES personnel(id)
        )
    ''')

    # ========== جدول دانش‌آموزان ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            national_code TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            father_name TEXT,
            grade TEXT NOT NULL,
            class_name TEXT NOT NULL,
            field TEXT,
            phone1 TEXT,
            phone2 TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            UNIQUE(school_id, national_code),
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
    ''')

    # ========== جدول حضور و غیاب ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT DEFAULT 'present',
            note TEXT,
            recorded_by TEXT,
            created_at TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(student_id, attendance_date)
        )
    ''')

    # ========== جدول تنظیمات ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            school_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            PRIMARY KEY (school_id, key)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("✅ جدول‌های دیتابیس ساخته شدند")