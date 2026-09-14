from flask import render_template, request, session, redirect, jsonify
import sqlite3
from core.database import get_db_connection
from core.logger import get_logger

logger = get_logger(__name__)


def login_page():
    if request.method == 'GET':
        session.pop('_flashes', None)
        return render_template('login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return render_template('login.html', error='❌ نام کاربری و رمز عبور را وارد کنید')

    if not username.isdigit() or not password.isdigit():
        return render_template('login.html', error='❌ نام کاربری و رمز عبور باید عددی باشند')

    if len(username) != 4 or len(password) != 4:
        return render_template('login.html', error='❌ نام کاربری و رمز عبور باید ۴ رقمی باشند')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, username, password, personnel_id, is_admin, is_super_admin, is_active
            FROM users WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return render_template('login.html', error='❌ نام کاربری یا رمز عبور اشتباه است')

        if user['password'] != password:
            return render_template('login.html', error='❌ نام کاربری یا رمز عبور اشتباه است')

        if not user['is_active']:
            return render_template('login.html', error='❌ این کاربر غیرفعال شده است')

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['personnel_id'] = user['personnel_id']
        session['is_admin'] = bool(user['is_admin'])
        session['is_super_admin'] = bool(user['is_super_admin'])

        return redirect('/')

    except Exception as e:
        logger.error(f"خطا در لاگین: {e}")
        return render_template('login.html', error='❌ خطای سرور در ورود به سیستم')


def logout():
    session.clear()
    return redirect('/login')


def refresh_session():
    if 'username' not in session:
        return jsonify({'error': 'ابتدا وارد شوید'})
    return jsonify({'success': True, 'message': 'Session معتبر است'})


def check_my_levels():
    if 'username' not in session:
        return jsonify({'error': 'ابتدا وارد شوید'})
    return jsonify({
        'username': session.get('username'),
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

        if not all([current_password, new_password, confirm_password]):
            return jsonify({'success': False, 'error': 'تمام فیلدها را پر کنید'})

        if not new_password.isdigit() or len(new_password) != 4:
            return jsonify({'success': False, 'error': 'رمز جدید باید ۴ رقمی باشد'})

        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'رمز جدید با تکرارش مطابقت ندارد'})

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()

        if not row or row['password'] != current_password:
            conn.close()
            return jsonify({'success': False, 'error': 'رمز فعلی اشتباه است'})

        cursor.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'رمز عبور تغییر کرد'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})