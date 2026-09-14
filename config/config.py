import os
import logging
from datetime import timedelta

# =====================================================
# مسیر پایه پروژه
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """تنظیمات پایه که همه محیط‌ها ازش ارث می‌برن"""

    # ========== Flask ==========
    SECRET_KEY = os.environ.get('SECRET_KEY', 'school-attendance-secret-2025')
    DEBUG = False
    TESTING = False

    # ========== دیتابیس ==========
    # مسیر دیتابیس SQLite رو کنار خود app.py می‌ذاریم
    DB_PATH = os.path.join(BASE_DIR, 'attendance.db')

    # ========== Session ==========
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = False   # چون روی HTTP تست می‌کنیم
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ========== Upload (برای امضای دیجیتال) ==========
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'signatures')

    # ========== Logging ==========
    LOG_LEVEL = 'INFO'

    # ========== Security ==========
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY', 'school-csrf-key-2025')

    # ========== اطلاعات برنامه ==========
    APP_NAME = "سیستم حضور و غیاب مدرسه"
    APP_VERSION = "1.0.0"

    # ========== تلگرام ==========
    # این‌ها رو بعداً توی فایل .env پر می‌کنیم (روی Render)
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_ENABLED = os.environ.get('TELEGRAM_ENABLED', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    """تنظیمات محیط توسعه (روی سیستم خودت)"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """تنظیمات محیط production (روی Render یا هاست ایرانی)"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SESSION_COOKIE_SECURE = False  # چون Render رایگان HTTPS داره ولی ساده‌تره False بذاریم


class TestingConfig(Config):
    """تنظیمات محیط تست"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    DB_PATH = ':memory:'


# =====================================================
# انتخاب کانفیگ بر اساس متغیر محیطی
# =====================================================
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """تشخیص خودکار محیط و برگرداندن کانفیگ مناسب"""
    env = os.environ.get('FLASK_ENV', 'development')
    config_class = config.get(env, config['default'])
    return config_class()


current_config = get_config()