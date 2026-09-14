from functools import wraps
from flask import session, redirect, jsonify, request


def check_access(permission):
    """بررسی دسترسی کاربر (برای استفاده داخل route)"""
    if session.get('is_super_admin'):
        return True
    return bool(session.get(permission, False))


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        if not (session.get('is_admin') or session.get('is_super_admin')):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'دسترسی غیرمجاز'}), 403
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


def super_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        if not session.get('is_super_admin'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'دسترسی غیرمجاز'}), 403
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated