import sqlite3
import logging
from contextlib import contextmanager
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
    """ایندکس‌های پروژه حضور و غیاب مدرسه"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_personnel_code
        ON personnel(personnel_code)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_attendance_date
        ON attendance(attendance_date)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_attendance_personnel
        ON attendance(personnel_id, attendance_date)
    ''')

    conn.commit()
    conn.close()
    print("✅ ایندکس‌های دیتابیس ایجاد شدند")

def create_default_super_admin():
    """ساخت کاربر Super Admin پیش‌فرض (1000) اگر وجود نداشته باشد"""
    import os
    from datetime import datetime

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users")
    result = cursor.fetchone()

    if result['count'] == 0:
        # رمز از Environment Variable خونده می‌شه (اگه نبود، پیش‌فرض 1000)
        admin_password = os.environ.get('SUPER_ADMIN_PASSWORD', '1000')

        # تاریخ امروز شمسی
        try:
            import jdatetime
            today = jdatetime.date.today().strftime('%Y/%m/%d')
        except Exception:
            today = datetime.now().strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO personnel (personnel_code, first_name, last_name, phone1, created_at)
            VALUES ('1000', 'مدیر', 'سیستم', '09120000000', ?)
        """, (today,))
        personnel_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (username, password, personnel_id, is_admin, is_super_admin, is_active, created_at)
            VALUES ('1000', ?, ?, 1, 1, 1, ?)
        """, (admin_password, personnel_id, today))

        conn.commit()
        print("✅ کاربر Super Admin پیش‌فرض ساخته شد (1000)")
    else:
        print("ℹ️ کاربران قبلاً وجود دارند، Super Admin ساخته نشد")

    conn.close()