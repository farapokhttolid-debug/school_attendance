from flask import Flask, render_template, request, session, redirect, jsonify
from datetime import datetime
import logging
from core.database import create_default_super_admin, create_indexes
from config.config import current_config
from core.logger import get_logger
from blueprints.database import init_db
from blueprints import students as students_bp
from blueprints.decorators import admin_required
from blueprints import attendance as attendance_bp
logger = get_logger(__name__)

app = Flask(__name__)
app.config.from_object(current_config)
app.secret_key = current_config.SECRET_KEY


@app.route('/students')
def students_page():
    return students_bp.students_page()


@app.route('/api/students/list')
def api_students_list():
    return students_bp.get_students()


@app.route('/api/students/add', methods=['POST'])
@admin_required
def api_students_add():
    return students_bp.add_student()


@app.route('/api/students/edit/<int:student_id>', methods=['POST'])
@admin_required
def api_students_edit(student_id):
    return students_bp.edit_student(student_id)


@app.route('/api/students/delete/<int:student_id>', methods=['POST'])
@admin_required
def api_students_delete(student_id):
    return students_bp.delete_student(student_id)


@app.route('/api/students/grades')
def api_students_grades():
    return students_bp.get_grades()


@app.route('/api/students/classes')
def api_students_classes():
    return students_bp.get_classes()

@app.route('/api/students/upload_excel', methods=['POST'])
@admin_required
def api_students_upload_excel():
    return students_bp.upload_excel()

@app.route('/attendance')
def attendance_page():
    return attendance_bp.attendance_page()


@app.route('/api/attendance/list')
def api_attendance_list():
    return attendance_bp.get_attendance_list()


@app.route('/api/attendance/save', methods=['POST'])
def api_attendance_save():
    return attendance_bp.save_attendance()


@app.route('/api/attendance/save_bulk', methods=['POST'])
def api_attendance_save_bulk():
    return attendance_bp.save_attendance_bulk()

_first_request_done = False

@app.before_request
def check_login():
    global _first_request_done
    if not _first_request_done:
        _first_request_done = True
        try:
            init_db()                      
            create_default_super_admin()
            create_indexes()
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