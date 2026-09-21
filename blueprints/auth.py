from flask import render_template, request, session, redirect, jsonify
from core.database import get_db_connection
from core.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


def get_schools_list():
    """لیست مدارس فعال برای صفحه ورود"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, code FROM schools WHERE is_active = 1 ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'schools': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def login_page():
    if request.method == 'GET':
        session.pop('_flashes', None)
        return render_template('login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    school_id = request.form.get('school_id', '').strip()
    is_super = request.form.get('is_super', '').strip()

    # اگه Super Admin (1000) هست، نیازی به انتخاب مدرسه نیست
    if username == '1000':
        school_id = None

    if not username or not password:
        return render_template('login.html', error='نام کاربری و رمز عبور را وارد کنید')

    if not username.isdigit() or not password.isdigit():
        return render_template('login.html', error='نام کاربری و رمز عبور باید عددی باشند')

    if len(username) != 4 or len(password) != 4:
        return render_template('login.html', error='نام کاربری و رمز عبور باید ۴ رقمی باشند')

    if username != '1000' and not school_id:
        return render_template('login.html', error='لطفاً مدرسه را انتخاب کنید')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if school_id:
            cursor.execute('''
                SELECT id, school_id, username, password, personnel_id, is_admin, is_super_admin, is_active
                FROM users WHERE username = ? AND school_id = ?
            ''', (username, school_id))
        else:
            cursor.execute('''
                SELECT id, school_id, username, password, personnel_id, is_admin, is_super_admin, is_active
                FROM users WHERE username = ? AND is_super_admin = 1
            ''', (username,))

        user = cursor.fetchone()
        conn.close()

        if not user or user['password'] != password:
            return render_template('login.html', error='نام کاربری یا رمز عبور اشتباه است')

        if not user['is_active']:
            return render_template('login.html', error='این کاربر غیرفعال شده است')

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['school_id'] = user['school_id']
        session['personnel_id'] = user['personnel_id']
        session['is_admin'] = bool(user['is_admin'])
        session['is_super_admin'] = bool(user['is_super_admin'])

        # نام مدرسه رو ذخیره کنیم
        if user['school_id']:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM schools WHERE id = ?", (user['school_id'],))
            school = cursor.fetchone()
            conn.close()
            session['school_name'] = school['name'] if school else ''
        else:
            session['school_name'] = 'مدیریت کل سیستم'

        return redirect('/')

    except Exception as e:
        logger.error(f"خطا در لاگین: {e}")
        return render_template('login.html', error='خطای سرور در ورود')


def logout():
    session.clear()
    return redirect('/login')


def refresh_session():
    if 'username' not in session:
        return jsonify({'error': 'ابتدا وارد شوید'})
    return jsonify({'success': True})


def check_my_levels():
    if 'username' not in session:
        return jsonify({'error': 'ابتدا وارد شوید'})
    return jsonify({
        'username': session.get('username'),
        'school_id': session.get('school_id'),
        'school_name': session.get('school_name'),
        'is_admin': session.get('is_admin'),
        'is_super_admin': session.get('is_super_admin')
    })


def change_my_password():
    try:
        if 'username' not in session:
            return jsonify({'success': False, 'error': 'ابتدا وارد شوید'})

        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        username = session['username']
        school_id = session.get('school_id')

        if not all([current_password, new_password, confirm_password]):
            return jsonify({'success': False, 'error': 'تمام فیلدها را پر کنید'})

        if not new_password.isdigit() or len(new_password) != 4:
            return jsonify({'success': False, 'error': 'رمز جدید باید ۴ رقمی باشد'})

        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'رمز جدید با تکرارش مطابقت ندارد'})

        conn = get_db_connection()
        cursor = conn.cursor()

        if school_id:
            cursor.execute('SELECT password FROM users WHERE username = ? AND school_id = ?', (username, school_id))
        else:
            cursor.execute('SELECT password FROM users WHERE username = ? AND is_super_admin = 1', (username,))

        row = cursor.fetchone()

        if not row or row['password'] != current_password:
            conn.close()
            return jsonify({'success': False, 'error': 'رمز فعلی اشتباه است'})

        if school_id:
            cursor.execute('UPDATE users SET password = ? WHERE username = ? AND school_id = ?', (new_password, username, school_id))
        else:
            cursor.execute('UPDATE users SET password = ? WHERE username = ? AND is_super_admin = 1', (new_password, username))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'رمز عبور تغییر کرد'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})