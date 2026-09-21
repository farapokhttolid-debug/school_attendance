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


def attendance_page():
    return render_template('attendance.html')


# =====================================================
# API: دریافت لیست دانش‌آموزان + وضعیت حضور امروز
# =====================================================
def get_attendance_list():
    try:
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
            WHERE s.is_active = 1
        '''
        params = [date]

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
# API: ذخیره وضعیت حضور یک دانش‌آموز
# =====================================================
def save_attendance():
    try:
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

        # چک وجود
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
# API: ذخیره گروهی (چندتا با هم)
# =====================================================
def save_attendance_bulk():
    try:
        data = request.get_json()
        items = data.get('items', [])
        date = data.get('date', '').strip() or get_today_jalali()
        recorded_by = session.get('username', '')

        if not items:
            return jsonify({'success': False, 'error': 'داده‌ای ارسال نشده'})

        conn = get_db_connection()
        cursor = conn.cursor()

        for item in items:
            student_id = item.get('student_id')
            status = item.get('status', 'present')
            note = item.get('note', '').strip()

            if not student_id:
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

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'{len(items)} رکورد ذخیره شد'})
    except Exception as e:
        logger.error(f"خطا در ذخیره گروهی: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500