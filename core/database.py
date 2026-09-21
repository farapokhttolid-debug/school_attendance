import sqlite3
import os
import logging
from contextlib import contextmanager
from datetime import datetime
from config.config import Config


class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self._connection_pool = []
        self.max_connections = 20

    def get_connection(self):
        if self._connection_pool:
            conn = self._connection_pool.pop()
            try:
                conn.execute("SELECT 1")
                conn.row_factory = sqlite3.Row
                return conn
            except:
                pass

        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def return_connection(self, conn):
        if conn and len(self._connection_pool) < self.max_connections:
            self._connection_pool.append(conn)
        elif conn:
            conn.close()

    @contextmanager
    def get_connection_context(self):
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {e}")
            raise
        finally:
            self.return_connection(conn)

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        with self.get_connection_context() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.lastrowid

    def close_all_connections(self):
        for conn in self._connection_pool:
            try:
                conn.close()
            except:
                pass
        self._connection_pool.clear()


db_manager = DatabaseManager()


def get_db_connection():
    return db_manager.get_connection()


def get_db_connection_context():
    return db_manager.get_connection_context()


def execute_sql(query, params=None):
    return db_manager.execute_query(query, params)


def create_indexes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_school ON users(school_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_school ON students(school_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_national ON students(national_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_grade_class ON students(school_id, grade, class_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id, attendance_date)')

    conn.commit()
    conn.close()
    print("✅ ایندکس‌های دیتابیس ایجاد شدند")


def create_default_super_admin():
    """ساخت کاربر Super Admin پیش‌فرض (1000) در اولین اجرا"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_super_admin = 1")
    result = cursor.fetchone()

    if result['count'] == 0:
        admin_password = os.environ.get('SUPER_ADMIN_PASSWORD', '1000')

        try:
            import jdatetime
            today = jdatetime.date.today().strftime('%Y/%m/%d')
        except Exception:
            today = datetime.now().strftime('%Y-%m-%d')

        # Super Admin: school_id = NULL (مالک کل سیستم)
        cursor.execute('''
            INSERT INTO users (school_id, username, password, is_admin, is_super_admin, is_active, created_at)
            VALUES (NULL, '1000', ?, 1, 1, 1, ?)
        ''', (admin_password, today))

        conn.commit()
        print("✅ کاربر Super Admin پیش‌فرض ساخته شد (1000)")
    else:
        print("ℹ️ Super Admin از قبل وجود دارد")

    conn.close()