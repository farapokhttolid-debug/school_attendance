from flask import render_template, request, jsonify, session
from core.database import get_db_connection
from core.logger import get_logger
from blueprints.decorators import super_admin_required
from datetime import datetime

logger = get_logger(__name__)


def get_today_jalali():
    try:
        import jdatetime
        return jdatetime.date.today().strftime('%Y/%m/%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')


def schools_page():
    return render_template('schools.html')


def list_schools():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, 
                (SELECT COUNT(*) FROM students WHERE school_id = s.id AND is_active = 1) as student_count,
                (SELECT COUNT(*) FROM users WHERE school_id = s.id AND is_active = 1) as user_count
            FROM schools s
            ORDER BY s.created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'schools': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@super_admin_required
def add_school():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        code = data.get('code', '').strip()
        address = data.get('address', '').strip()
        phone = data.get('phone', '').strip()

        if not name or not code:
            return jsonify({'success': False, 'error': 'نام و کد مدرسه اجباری است'})

        if not code.isalnum():
            return jsonify({'success': False, 'error': 'کد مدرسه فقط حروف و عدد'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM schools WHERE code = ?", (code,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'این کد مدرسه قبلاً ثبت شده'})

        cursor.execute('''
            INSERT INTO schools (name, code, address, phone, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (name, code, address, phone, get_today_jalali()))

        conn.commit()
        school_id = cursor.lastrowid
        conn.close()

        return jsonify({'success': True, 'message': 'مدرسه ساخته شد', 'school_id': school_id})
    except Exception as e:
        logger.error(f"خطا در ساخت مدرسه: {e}")
        return jsonify({'success': False, 'error': str(e)})


@super_admin_required
def edit_school(school_id):
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        address = data.get('address', '').strip()
        phone = data.get('phone', '').strip()

        if not name:
            return jsonify({'success': False, 'error': 'نام مدرسه اجباری است'})

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE schools SET name = ?, address = ?, phone = ?
            WHERE id = ?
        ''', (name, address, phone, school_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'تغییرات ذخیره شد'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@super_admin_required
def toggle_school(school_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM schools WHERE id = ?", (school_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'مدرسه یافت نشد'})

        new_status = 0 if row['is_active'] else 1
        cursor.execute("UPDATE schools SET is_active = ? WHERE id = ?", (new_status, school_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'وضعیت تغییر کرد', 'is_active': new_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@super_admin_required
def enter_school(school_id):
    """1000 وارد یه مدرسه می‌شه (برای مدیریت)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM schools WHERE id = ? AND is_active = 1", (school_id,))
        school = cursor.fetchone()
        conn.close()

        if not school:
            return jsonify({'success': False, 'error': 'مدرسه یافت نشد یا غیرفعال است'})

        session['school_id'] = school['id']
        session['school_name'] = school['name']

        return jsonify({'success': True, 'message': f'وارد مدرسه {school["name"]} شدید'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@super_admin_required
def exit_school():
    """خروج 1000 از یه مدرسه"""
    session['school_id'] = None
    session['school_name'] = 'مدیریت کل سیستم'
    return jsonify({'success': True})