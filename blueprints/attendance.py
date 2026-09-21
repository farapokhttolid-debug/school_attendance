from flask import render_template, request, jsonify, session
from core.database import get_db_connection
from core.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


def get_today_jalali():
    try:
        import jdatetime
        return jdatetime.date.today().strftime('%Y/%m/%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')


def get_current_school_id():
    return session.get('school_id')


def attendance_page():
    return render_template('attendance.html')


def get_today_date():
    return jsonify({'date': get_today_jalali()})


# =====================================================
# لیست حضور
# =====================================================
def get_attendance_list():
    try:
        school_id = get_current_school_id()
        if not school_id:
            return jsonify({'success': False, 'error': 'مدرسه انتخاب نشده'})

        grade = request.args.get('grade', '').strip()
        class_name = request.args.get('class_name', '').strip()
        search = request.args.get('search', '').strip()
        date = request.args.get('date', '').strip() or get_today_jalali()

        query = '''
            SELECT 
                s.id, s.national_code, s.first_name, s.last_name,
                s.grade, s.class_name,
                COALESCE(a.status, 'present') as status,
                COALESCE(a.note, '') as note
            FROM students s
            LEFT JOIN attendance a 
                ON s.id = a.student_id AND a.attendance_date = ?
            WHERE s.is_active = 1 AND s.school_id = ?
        '''
        params = [date, school_id]

        if grade:
            query += " AND s.grade = ?"
            params.append(grade)
        if class_name:
            query += " AND s.class_name = ?"
            params.append(class_name)
        if search:
            query += " AND (s.first_name LIKE ? OR s.last_name LIKE ? OR s.national_code LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like, like])

        query += " ORDER BY s.grade, s.class_name, s.last_name, s.first_name"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return jsonify({
            'success': True,
            'students': [dict(r) for r in rows],
            'date': date,
            'count': len(rows)
        })
    except Exception as e:
        logger.error(f"خطا در لیست حضور: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# ذخیره یک رکورد
# =====================================================
def save_attendance():
    try:
        school_id = get_current_school_id()
        data = request.get_json()
        student_id = data.get('student_id')
        status = data.get('status', 'present')
        note = data.get('note', '').strip()
        date = data.get('date', '').strip() or get_today_jalali()

        if not student_id:
            return jsonify({'success': False, 'error': 'شناسه دانش‌آموز نامعتبر'})

        if status not in ['present', 'absent', 'leave', 'late']:
            return jsonify({'success': False, 'error': 'وضعیت نامعتبر'})

        conn = get_db_connection()
        cursor = conn.cursor()

        # چک کن دانش‌آموز مال همین مدرسه باشه
        cursor.execute("SELECT id FROM students WHERE id = ? AND school_id = ?", (student_id, school_id))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'دانش‌آموز یافت نشد'})

        cursor.execute(
            "SELECT id FROM attendance WHERE student_id = ? AND attendance_date = ?",
            (student_id, date)
        )
        existing = cursor.fetchone()

        recorded_by = session.get('username', '')

        if existing:
            cursor.execute('''
                UPDATE attendance SET status = ?, note = ?, recorded_by = ?
                WHERE id = ?
            ''', (status, note, recorded_by, existing['id']))
        else:
            cursor.execute('''
                INSERT INTO attendance (student_id, attendance_date, status, note, recorded_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, date, status, note, recorded_by, datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'ذخیره شد'})
    except Exception as e:
        logger.error(f"خطا در ذخیره حضور: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# ذخیره گروهی
# =====================================================
def save_attendance_bulk():
    try:
        school_id = get_current_school_id()
        data = request.get_json()
        items = data.get('items', [])
        date = data.get('date', '').strip() or get_today_jalali()
        recorded_by = session.get('username', '')

        if not items:
            return jsonify({'success': False, 'error': 'داده‌ای ارسال نشده'})

        conn = get_db_connection()
        cursor = conn.cursor()

        # لیست دانش‌آموزان این مدرسه
        cursor.execute("SELECT id FROM students WHERE school_id = ? AND is_active = 1", (school_id,))
        valid_ids = {row['id'] for row in cursor.fetchall()}

        saved = 0
        for item in items:
            student_id = item.get('student_id')
            status = item.get('status', 'present')
            note = item.get('note', '').strip()

            if not student_id or student_id not in valid_ids:
                continue
            if status not in ['present', 'absent', 'leave', 'late']:
                continue

            cursor.execute(
                "SELECT id FROM attendance WHERE student_id = ? AND attendance_date = ?",
                (student_id, date)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute('''
                    UPDATE attendance SET status = ?, note = ?, recorded_by = ?
                    WHERE id = ?
                ''', (status, note, recorded_by, existing['id']))
            else:
                cursor.execute('''
                    INSERT INTO attendance (student_id, attendance_date, status, note, recorded_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (student_id, date, status, note, recorded_by, datetime.now().isoformat()))
            saved += 1

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'{saved} رکورد ذخیره شد'})
    except Exception as e:
        logger.error(f"خطا در ذخیره گروهی: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500