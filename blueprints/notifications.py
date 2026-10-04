from flask import render_template, request, jsonify, session
from core.database import get_db_connection
from core.logger import get_logger
from core.notifier import send_to_parent
from blueprints.decorators import admin_required
from datetime import datetime
from core.activity import log_activity

logger = get_logger(__name__)


def get_today_jalali():
    try:
        import jdatetime
        return jdatetime.date.today().strftime('%Y/%m/%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')


def notifications_page():
    return render_template('notifications.html')


# =====================================================
# لیست غایب‌های یه تاریخ
# =====================================================
@admin_required
def get_absent_list():
    try:
        school_id = session.get('school_id')
        date = request.args.get('date', '').strip() or get_today_jalali()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                s.id as student_id, s.national_code, s.first_name, s.last_name,
                s.grade, s.class_name,
                a.status, a.note,
                pc.platform, pc.chat_id
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            LEFT JOIN parent_contacts pc ON s.id = pc.student_id
            WHERE s.school_id = ? AND a.attendance_date = ? AND a.status = 'absent'
            ORDER BY s.grade, s.class_name, s.last_name
        ''', (school_id, date))

        rows = cursor.fetchall()
        conn.close()

        students = {}
        for r in rows:
            sid = r['student_id']
            if sid not in students:
                students[sid] = {
                    'student_id': sid,
                    'national_code': r['national_code'],
                    'first_name': r['first_name'],
                    'last_name': r['last_name'],
                    'grade': r['grade'],
                    'class_name': r['class_name'],
                    'note': r['note'] or '',
                    'contacts': []
                }
            if r['platform'] and r['chat_id']:
                students[sid]['contacts'].append({
                    'platform': r['platform'],
                    'chat_id': r['chat_id']
                })

        # نام مدرسه
        cursor = get_db_connection().cursor()
        cursor.execute("SELECT name FROM schools WHERE id = ?", (school_id,))
        school = cursor.fetchone()
        school_name = school['name'] if school else ''

        return jsonify({
            'success': True,
            'students': list(students.values()),
            'count': len(students),
            'date': date,
            'school_name': school_name
        })
    except Exception as e:
        logger.error(f"خطا در لیست غایب: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# ارسال پیام به والدین
# =====================================================
@admin_required
def send_notifications():
    try:
        school_id = session.get('school_id')
        data = request.get_json()
        date = data.get('date', '').strip() or get_today_jalali()
        student_ids = data.get('student_ids', [])

        if not student_ids:
            return jsonify({'success': False, 'error': 'دانش‌آموزی انتخاب نشده'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM schools WHERE id = ?", (school_id,))
        school = cursor.fetchone()
        school_name = school['name'] if school else 'مدرسه'

        results = []
        success_count = 0
        error_count = 0

        for sid in student_ids:
            cursor.execute('''
                SELECT s.first_name, s.last_name, pc.platform, pc.chat_id
                FROM students s
                LEFT JOIN parent_contacts pc ON s.id = pc.student_id
                WHERE s.id = ? AND s.school_id = ?
            ''', (sid, school_id))

            rows = cursor.fetchall()
            if not rows:
                continue

            first_name = rows[0]['first_name']
            last_name = rows[0]['last_name']

            message = (
                f"سلام\n"
                f"{first_name} {last_name} عزیز امروز {date} در مدرسه {school_name} غایب بوده است.\n"
                f"لطفاً در صورت نیاز با مدرسه تماس بگیرید."
            )

            sent_any = False
            for r in rows:
                if r['platform'] and r['chat_id']:
                    ok, msg = send_to_parent(r['platform'], r['chat_id'], message)
                    if ok:
                        success_count += 1
                        sent_any = True
                    else:
                        error_count += 1
                        results.append(f"{first_name} {last_name} ({r['platform']}): {msg}")

            if not sent_any:
                results.append(f"{first_name} {last_name}: هیچ chat_id ثبت نشده")

        conn.close()
        log_activity('send_notification', 'student', None, f"{success_count} پیام برای {date}")

        return jsonify({
            'success': True,
            'message': f'{success_count} پیام ارسال شد، {error_count} خطا',
            'success_count': success_count,
            'error_count': error_count,
            'details': results[:30]
        })
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# ذخیره chat_id والدین
# =====================================================
@admin_required
def save_parent_contact():
    try:
        school_id = session.get('school_id')
        data = request.get_json()
        student_id = data.get('student_id')
        platform = data.get('platform')
        chat_id = data.get('chat_id', '').strip()

        if not student_id or not platform:
            return jsonify({'success': False, 'error': 'اطلاعات ناقص'})

        if platform not in ['telegram', 'bale']:
            return jsonify({'success': False, 'error': 'پلتفرم نامعتبر'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM students WHERE id = ? AND school_id = ?", (student_id, school_id))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'دانش‌آموز یافت نشد'})

        if chat_id:
            cursor.execute('''
                INSERT OR REPLACE INTO parent_contacts (student_id, platform, chat_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (student_id, platform, chat_id, get_today_jalali()))
        else:
            cursor.execute(
                "DELETE FROM parent_contacts WHERE student_id = ? AND platform = ?",
                (student_id, platform)
            )

        conn.commit()
        conn.close()
        log_activity('save_parent_contact', 'student', student_id, f"{platform}")

        return jsonify({'success': True, 'message': 'ذخیره شد'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# دریافت chat_idهای یه دانش‌آموز
# =====================================================
@admin_required
def get_parent_contacts(student_id):
    try:
        school_id = session.get('school_id')
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM students WHERE id = ? AND school_id = ?", (student_id, school_id))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'دانش‌آموز یافت نشد'})

        cursor.execute(
            "SELECT platform, chat_id FROM parent_contacts WHERE student_id = ?",
            (student_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        contacts = {r['platform']: r['chat_id'] for r in rows}
        return jsonify({'success': True, 'contacts': contacts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500