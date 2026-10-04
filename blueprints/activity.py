from flask import render_template, request, jsonify, session
from core.database import get_db_connection
from core.logger import get_logger
from blueprints.decorators import admin_required

logger = get_logger(__name__)


def activity_page():
    return render_template('activity.html')


@admin_required
def list_activities():
    try:
        school_id = session.get('school_id')
        username = request.args.get('username', '').strip()
        action = request.args.get('action', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()

        query = "SELECT * FROM activity_log WHERE 1=1"
        params = []

        if school_id:
            query += " AND (school_id = ? OR school_id IS NULL)"
            params.append(school_id)
        else:
            query += " AND school_id IS NULL"

        if username:
            query += " AND username = ?"
            params.append(username)
        if action:
            query += " AND action = ?"
            params.append(action)
        if date_from:
            query += " AND created_at >= ?"
            params.append(date_from)
        if date_to:
            query += " AND created_at <= ?"
            params.append(date_to + ' 23:59:59')

        query += " ORDER BY id DESC LIMIT 500"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return jsonify({
            'success': True,
            'activities': [dict(r) for r in rows],
            'count': len(rows)
        })
    except Exception as e:
        logger.error(f"خطا در لیست لاگ: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_required
def get_action_types():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT action FROM activity_log ORDER BY action")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'actions': [r['action'] for r in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_required
def get_users():
    try:
        school_id = session.get('school_id')
        conn = get_db_connection()
        cursor = conn.cursor()

        if school_id:
            cursor.execute(
                "SELECT DISTINCT username FROM activity_log WHERE school_id = ? ORDER BY username",
                (school_id,)
            )
        else:
            cursor.execute("SELECT DISTINCT username FROM activity_log WHERE school_id IS NULL ORDER BY username")

        rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'users': [r['username'] for r in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500