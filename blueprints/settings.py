from flask import render_template, request, jsonify, session
from core.database import get_db_connection
from core.logger import get_logger
from blueprints.decorators import admin_required
from datetime import datetime

logger = get_logger(__name__)


def settings_page():
    return render_template('settings.html')


# =====================================================
# لیست تنظیمات مدرسه
# =====================================================
def get_settings():
    try:
        school_id = session.get('school_id')
        if not school_id:
            return jsonify({'success': False, 'error': 'مدرسه انتخاب نشده'})

        conn = get_db_connection()
        cursor = conn.cursor()

        # تنظیمات مدرسه
        cursor.execute("SELECT key, value FROM settings WHERE school_id = ?", (school_id,))
        rows = cursor.fetchall()
        settings = {row['key']: row['value'] for row in rows}

        # اطلاعات مدرسه از جدول schools
        cursor.execute("SELECT name, address, phone FROM schools WHERE id = ?", (school_id,))
        school = cursor.fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'settings': {
                'school_name': school['name'] if school else '',
                'address': school['address'] if school else '',
                'phone': school['phone'] if school else '',
                'academic_year': settings.get('academic_year', ''),
                'principal_name': settings.get('principal_name', ''),
                'grades_list': settings.get('grades_list', '')
            }
        })
    except Exception as e:
        logger.error(f"خطا در دریافت تنظیمات: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# ذخیره تنظیمات
# =====================================================
@admin_required
def save_settings():
    try:
        school_id = session.get('school_id')
        if not school_id:
            return jsonify({'success': False, 'error': 'مدرسه انتخاب نشده'})

        data = request.get_json()

        school_name = data.get('school_name', '').strip()
        address = data.get('address', '').strip()
        phone = data.get('phone', '').strip()
        academic_year = data.get('academic_year', '').strip()
        principal_name = data.get('principal_name', '').strip()
        grades_list = data.get('grades_list', '').strip()

        if not school_name:
            return jsonify({'success': False, 'error': 'نام مدرسه اجباری است'})

        conn = get_db_connection()
        cursor = conn.cursor()

        # به‌روزرسانی جدول schools
        cursor.execute('''
            UPDATE schools SET name = ?, address = ?, phone = ?
            WHERE id = ?
        ''', (school_name, address, phone, school_id))

        # ذخیره تنظیمات اضافی
        for key, value in [
            ('academic_year', academic_year),
            ('principal_name', principal_name),
            ('grades_list', grades_list)
        ]:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (school_id, key, value)
                VALUES (?, ?, ?)
            ''', (school_id, key, value))

        conn.commit()
        conn.close()

        # به‌روزرسانی نام مدرسه توی session
        session['school_name'] = school_name

        return jsonify({'success': True, 'message': 'تنظیمات ذخیره شد'})
    except Exception as e:
        logger.error(f"خطا در ذخیره تنظیمات: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# لیست پایه‌ها (برای فیلترها و فرم‌ها)
# =====================================================
def get_grades_from_settings():
    try:
        school_id = session.get('school_id')
        if not school_id:
            return jsonify({'success': True, 'grades': []})

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE school_id = ? AND key = 'grades_list'", (school_id,))
        row = cursor.fetchone()
        conn.close()

        if row and row['value']:
            grades = [g.strip() for g in row['value'].split(',') if g.strip()]
        else:
            grades = []

        return jsonify({'success': True, 'grades': grades})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500