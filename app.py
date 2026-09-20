from flask import Flask, render_template, request, session, redirect, jsonify
from datetime import datetime
import logging
from core.database import create_default_super_admin
from config.config import current_config
from core.logger import get_logger
from blueprints.database import init_db

logger = get_logger(__name__)

app = Flask(__name__)
app.config.from_object(current_config)
app.secret_key = current_config.SECRET_KEY


# ========== ثبت Blueprint ها ==========
# بعداً که فایل‌های جدید رو ساختیم، اینجا اضافه می‌کنیم


_first_request_done = False

@app.before_request
def check_login():
    global _first_request_done
    if not _first_request_done:
        _first_request_done = True
        try:
            init_db()                      
            create_default_super_admin()
        except Exception as e:
            logger.error(f"خطا در راه‌اندازی اولیه: {e}")

    public_routes = ['login_page', 'static', 'health_check']
    if request.endpoint and request.endpoint not in public_routes:
        if 'user_id' not in session:
            return redirect('/login')
# ========== مسیرهای اصلی ==========
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    from blueprints.auth import login_page as lp
    return lp()


@app.route('/logout')
def logout():
    from blueprints.auth import logout as lo
    return lo()


@app.route('/api/refresh_session', methods=['GET', 'POST'])
def refresh_session():
    from blueprints.auth import refresh_session as rs
    return rs()


@app.route('/api/change_my_password', methods=['POST'])
def change_my_password():
    from blueprints.auth import change_my_password as cmp
    return cmp()


@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': current_config.APP_VERSION
    })


@app.context_processor
def utility_processor():
    return {'now': datetime.now}


if __name__ == '__main__':
    init_db()
    logger.info("🚀 سرور Flask در حال اجرا روی پورت 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)