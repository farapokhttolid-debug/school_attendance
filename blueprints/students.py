from flask import render_template, request, jsonify, session, redirect
from core.database import get_db_connection
from core.logger import get_logger
from blueprints.decorators import admin_required
from datetime import datetime

logger = get_logger(__name__)


def get_today_jalali():
    """تاریخ امروز شمسی"""
    try:
        import jdatetime
        return jdatetime.date.today().strftime('%Y/%m/%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')


# =====================================================
# صفحه اصلی مدیریت دانش‌آموزان
# =====================================================
def students_page():
    return render_template('students.html')


# =====================================================
# API: لیست دانش‌آموزان با فیلتر
# =====================================================
def get_students():
    try:
        grade = request.args.get('grade', '').strip()
        class_name = request.args.get('class_name', '').strip()
        search = request.args.get('search', '').strip()

        query = "SELECT * FROM students WHERE is_active = 1"
        params = []

        if grade:
            query += " AND grade = ?"
            params.append(grade)
        if class_name:
            query += " AND class_name = ?"
            params.append(class_name)
        if search:
            query += """ AND (
                first_name LIKE ? OR
                last_name LIKE ? OR
                national_code LIKE ? OR
                father_name LIKE ?
            )"""
            like = f"%{search}%"
            params.extend([like, like, like, like])

        query += " ORDER BY grade, class_name, last_name, first_name"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        students = [dict(row) for row in rows]
        return jsonify({'success': True, 'students': students, 'count': len(students)})

    except Exception as e:
        logger.error(f"خطا در دریافت دانش‌آموزان: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# API: افزودن دانش‌آموز
# =====================================================
@admin_required
def add_student():
    try:
        data = request.get_json()

        national_code = data.get('national_code', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        father_name = data.get('father_name', '').strip()
        grade = data.get('grade', '').strip()
        class_name = data.get('class_name', '').strip()
        field = data.get('field', '').strip()
        phone1 = data.get('phone1', '').strip()
        phone2 = data.get('phone2', '').strip()

        # اعتبارسنجی
        if not national_code or not first_name or not last_name or not grade or not class_name:
            return jsonify({'success': False, 'error': 'فیلدهای اجباری را پر کنید'})

        if len(national_code) != 10 or not national_code.isdigit():
            return jsonify({'success': False, 'error': 'کد ملی باید ۱۰ رقم عددی باشد'})

        conn = get_db_connection()
        cursor = conn.cursor()

        # چک تکراری نبودن
        cursor.execute("SELECT id FROM students WHERE national_code = ?", (national_code,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'این کد ملی قبلاً ثبت شده است'})

        cursor.execute('''
            INSERT INTO students
            (national_code, first_name, last_name, father_name, grade, class_name, field, phone1, phone2, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (national_code, first_name, last_name, father_name, grade, class_name, field, phone1, phone2, get_today_jalali()))

        conn.commit()
        student_id = cursor.lastrowid
        conn.close()

        return jsonify({'success': True, 'message': 'دانش‌آموز اضافه شد', 'id': student_id})

    except Exception as e:
        logger.error(f"خطا در افزودن دانش‌آموز: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# API: ویرایش دانش‌آموز
# =====================================================
@admin_required
def edit_student(student_id):
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM students WHERE id = ?", (student_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'دانش‌آموز یافت نشد'})

        cursor.execute('''
            UPDATE students SET
                first_name = ?,
                last_name = ?,
                father_name = ?,
                grade = ?,
                class_name = ?,
                field = ?,
                phone1 = ?,
                phone2 = ?
            WHERE id = ?
        ''', (
            data.get('first_name', '').strip(),
            data.get('last_name', '').strip(),
            data.get('father_name', '').strip(),
            data.get('grade', '').strip(),
            data.get('class_name', '').strip(),
            data.get('field', '').strip(),
            data.get('phone1', '').strip(),
            data.get('phone2', '').strip(),
            student_id
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'تغییرات ذخیره شد'})

    except Exception as e:
        logger.error(f"خطا در ویرایش: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# API: حذف دانش‌آموز (غیرفعال کردن)
# =====================================================
@admin_required
def delete_student(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET is_active = 0 WHERE id = ?", (student_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'دانش‌آموز حذف شد'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# API: لیست پایه‌ها (برای فیلتر)
# =====================================================
def get_grades():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT grade FROM students WHERE is_active = 1 ORDER BY grade")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'grades': [row['grade'] for row in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# API: لیست کلاس‌ها (برای فیلتر)
# =====================================================
def get_classes():
    try:
        grade = request.args.get('grade', '').strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        if grade:
            cursor.execute("SELECT DISTINCT class_name FROM students WHERE is_active = 1 AND grade = ? ORDER BY class_name", (grade,))
        else:
            cursor.execute("SELECT DISTINCT class_name FROM students WHERE is_active = 1 ORDER BY class_name")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'classes': [row['class_name'] for row in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500