from flask import Flask, render_template, request, session, redirect, jsonify
from datetime import datetime
import logging

from config.config import current_config
from core.logger import get_logger
from core.database import create_default_super_admin, create_indexes
from blueprints.database import init_db
from blueprints.decorators import admin_required, super_admin_required

from blueprints import auth as auth_bp
from blueprints import schools as schools_bp
from blueprints import students as students_bp
from blueprints import attendance as attendance_bp
from blueprints import reports as reports_bp
from blueprints import users as users_bp
from blueprints import settings as settings_bp

logger = get_logger(__name__)

app = Flask(__name__)
app.config.from_object(current_config)
app.secret_key = current_config.SECRET_KEY


# =====================================================
# راه‌اندازی اولیه
# =====================================================
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

    public_routes = ['login_page', 'static', 'health_check', 'api_schools_list']
    if request.endpoint and request.endpoint not in public_routes:
        if 'user_id' not in session:
            return redirect('/login')


# =====================================================
# صفحات اصلی
# =====================================================
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    # اگه Super Admin بود و مدرسه انتخاب نکرده، بره به مدیریت مدارس
    if session.get('is_super_admin') and not session.get('school_id'):
        return redirect('/schools')
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': current_config.APP_VERSION
    })


# =====================================================
# احراز هویت
# =====================================================
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    return auth_bp.login_page()


@app.route('/logout')
def logout():
    return auth_bp.logout()


@app.route('/api/refresh_session', methods=['GET', 'POST'])
def refresh_session():
    return auth_bp.refresh_session()


@app.route('/api/check_my_levels')
def check_my_levels():
    return auth_bp.check_my_levels()


@app.route('/api/change_my_password', methods=['POST'])
def change_my_password():
    return auth_bp.change_my_password()


@app.route('/api/schools_list')
def api_schools_list():
    return auth_bp.get_schools_list()

# =====================================================
# تنظیمات مدرسه
# =====================================================
@app.route('/settings')
@admin_required
def settings_page():
    return settings_bp.settings_page()


@app.route('/api/settings/get')
@admin_required
def api_settings_get():
    return settings_bp.get_settings()


@app.route('/api/settings/save', methods=['POST'])
@admin_required
def api_settings_save():
    return settings_bp.save_settings()


@app.route('/api/settings/grades')
def api_settings_grades():
    return settings_bp.get_grades_from_settings()


# =====================================================
# مدیریت مدارس (فقط Super Admin)
# =====================================================
@app.route('/schools')
@super_admin_required
def schools_page():
    return schools_bp.schools_page()


@app.route('/api/schools/list')
@super_admin_required
def api_schools_list_admin():
    return schools_bp.list_schools()


@app.route('/api/schools/add', methods=['POST'])
@super_admin_required
def api_schools_add():
    return schools_bp.add_school()


@app.route('/api/schools/edit/<int:school_id>', methods=['POST'])
@super_admin_required
def api_schools_edit(school_id):
    return schools_bp.edit_school(school_id)


@app.route('/api/schools/toggle/<int:school_id>', methods=['POST'])
@super_admin_required
def api_schools_toggle(school_id):
    return schools_bp.toggle_school(school_id)


@app.route('/api/schools/enter/<int:school_id>', methods=['POST'])
@super_admin_required
def api_schools_enter(school_id):
    return schools_bp.enter_school(school_id)


@app.route('/api/schools/exit', methods=['POST'])
@super_admin_required
def api_schools_exit():
    return schools_bp.exit_school()

@app.route('/profile')
def profile_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('profile.html')

# =====================================================
# مدیریت کاربران
# =====================================================
@app.route('/users')
@admin_required
def users_page():
    return users_bp.users_page()


@app.route('/api/users/list')
@admin_required
def api_users_list():
    return users_bp.list_users()


@app.route('/api/users/add', methods=['POST'])
@admin_required
def api_users_add():
    return users_bp.add_user()


@app.route('/api/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def api_users_delete(user_id):
    return users_bp.delete_user(user_id)


@app.route('/api/users/change_password/<int:user_id>', methods=['POST'])
@admin_required
def api_users_change_password(user_id):
    return users_bp.change_user_password(user_id)


@app.route('/api/users/schools')
def api_users_schools():
    return users_bp.list_schools_for_user()


# =====================================================
# مدیریت دانش‌آموزان
# =====================================================
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


# =====================================================
# حضور و غیاب
# =====================================================
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


@app.route('/api/attendance/today')
def api_attendance_today():
    return attendance_bp.get_today_date()


# =====================================================
# گزارش‌ها
# =====================================================
@app.route('/reports')
def reports_page():
    return reports_bp.reports_page()


@app.route('/api/reports/data')
def api_reports_data():
    return reports_bp.get_report()


@app.route('/api/reports/export')
@admin_required
def api_reports_export():
    return reports_bp.export_excel()


# =====================================================
# Context Processor
# =====================================================
@app.context_processor
def utility_processor():
    return {
        'now': datetime.now,
        'session': session
    }


if __name__ == '__main__':
    init_db()
    create_default_super_admin()
    create_indexes()
    logger.info("🚀 سرور Flask در حال اجرا روی پورت 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)