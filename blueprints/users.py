from flask import render_template, request, jsonify, session
from core.database import get_db_connection
from core.logger import get_logger
from blueprints.decorators import admin_required
from datetime import datetime

logger = get_logger(__name__)


def get_today_jalali():
    try:
        import jdatetime
        return jdatetime.date.today().strftime('%Y/%m/%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')


def users_page():
    return render_template('users.html')


# =====================================================
# لیست کاربران (بر اساس school_id)
# =====================================================
@admin_required
def list_users():
    try:
        school_id = session.get('school_id')
        is_super = session.get('is_super_admin')

        conn = get_db_connection()
        cursor = conn.cursor()

        if is_super and not school_id:
            # 1000 در حالت مدیریت کل: همه کاربران
            cursor.execute('''
                SELECT u.id, u.username, u.school_id, u.is_admin, u.is_super_admin, u.is_active, u.created_at,
                       s.name as school_name
                FROM users u
                LEFT JOIN schools s ON u.school_id = s.id
                ORDER BY u.is_super_admin DESC, s.name, u.username
            ''')
        else:
            # کاربران یه مدرسه خاص
            cursor.execute('''
                SELECT u.id, u.username, u.school_id, u.is_admin, u.is_super_admin, u.is_active, u.created_at,
                       s.name as school_name
                FROM users u
                LEFT JOIN schools s ON u.school_id = s.id
                WHERE u.school_id = ?
                ORDER BY u.is_admin DESC, u.username
            ''', (school_id,))

        rows = cursor.fetchall()
        conn.close()

        users = []
        for r in rows:
            d = dict(r)
            d['role'] = 'super_admin' if d['is_super_admin'] else ('admin' if d['is_admin'] else 'user')
            users.append(d)

        return jsonify({'success': True, 'users': users})
    except Exception as e:
        logger.error(f"خطا در لیست کاربران: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# افزودن کاربر
# =====================================================
@admin_required
def add_user():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'user').strip()

        is_super = session.get('is_super_admin')
        current_school_id = session.get('school_id')

        # انتخاب school_id
        if is_super and not current_school_id:
            # 1000 می‌تونه برای هر مدرسه کاربر بسازه
            school_id = data.get('school_id')
            if not school_id:
                return jsonify({'success': False, 'error': 'مدرسه را انتخاب کنید'})
        else:
            school_id = current_school_id

        # اعتبارسنجی
        if not username or not password:
            return jsonify({'success': False, 'error': 'نام کاربری و رمز عبور اجباری است'})

        if not username.isdigit() or len(username) != 4:
            return jsonify({'success': False, 'error': 'نام کاربری باید ۴ رقم عددی باشد'})

        if not password.isdigit() or len(password) != 4:
            return jsonify({'success': False, 'error': 'رمز عبور باید ۴ رقم عددی باشد'})

        if username == '1000':
            return jsonify({'success': False, 'error': 'کد 1000 رزرو شده است'})

        if role not in ['admin', 'user']:
            return jsonify({'success': False, 'error': 'نقش نامعتبر'})

        # فقط 1000 می‌تونه ادمین بسازه
        is_admin_new = 1 if role == 'admin' else 0
        if is_admin_new and not is_super:
            return jsonify({'success': False, 'error': 'فقط مدیر کل می‌تواند ادمین بسازد'})

        conn = get_db_connection()
        cursor = conn.cursor()

        # چک تکراری در همون مدرسه
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND school_id = ?",
            (username, school_id)
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'این نام کاربری قبلاً در این مدرسه ثبت شده'})

        cursor.execute('''
            INSERT INTO users (school_id, username, password, is_admin, is_super_admin, is_active, created_at)
            VALUES (?, ?, ?, ?, 0, 1, ?)
        ''', (school_id, username, password, is_admin_new, get_today_jalali()))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'کاربر ساخته شد'})
    except Exception as e:
        logger.error(f"خطا در ساخت کاربر: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# حذف/غیرفعال کردن کاربر
# =====================================================
@admin_required
def delete_user(user_id):
    try:
        is_super = session.get('is_super_admin')
        current_school_id = session.get('school_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        # کاربر هدف رو بگیر
        cursor.execute("SELECT username, school_id, is_super_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'کاربر یافت نشد'})

        # خودت رو حذف نکن
        if user['username'] == session.get('username'):
            conn.close()
            return jsonify({'success': False, 'error': 'نمی‌توانید خودتان را حذف کنید'})

        # محافظت از 1000
        if user['is_super_admin']:
            conn.close()
            return jsonify({'success': False, 'error': 'نمی‌توانید مدیر کل را حذف کنید'})

        # اگه ادمین مدرسه هست، فقط کاربران مدرسه خودش رو ببینه
        if not is_super:
            if user['school_id'] != current_school_id:
                conn.close()
                return jsonify({'success': False, 'error': 'دسترسی غیرمجاز'})

        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'کاربر حذف شد'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# تغییر رمز کاربر (توسط ادمین)
# =====================================================
@admin_required
def change_user_password(user_id):
    try:
        data = request.get_json()
        new_password = data.get('new_password', '').strip()

        if not new_password.isdigit() or len(new_password) != 4:
            return jsonify({'success': False, 'error': 'رمز جدید باید ۴ رقمی باشد'})

        is_super = session.get('is_super_admin')
        current_school_id = session.get('school_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT username, school_id, is_super_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'کاربر یافت نشد'})

        if user['is_super_admin'] and not is_super:
            conn.close()
            return jsonify({'success': False, 'error': 'دسترسی غیرمجاز'})

        if not is_super and user['school_id'] != current_school_id:
            conn.close()
            return jsonify({'success': False, 'error': 'دسترسی غیرمجاز'})

        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'رمز عبور تغییر کرد'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# لیست مدارس (برای انتخاب در فرم ساخت کاربر - فقط 1000)
# =====================================================
def list_schools_for_user():
    try:
        if not session.get('is_super_admin'):
            return jsonify({'success': False, 'error': 'دسترسی غیرمجاز'})

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, code FROM schools WHERE is_active = 1 ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'schools': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500