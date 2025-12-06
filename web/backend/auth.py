"""
Authentication module for the TikTok Battle Simulator dashboard.
Simple session-based authentication with password hashing.
"""

import hashlib
import secrets
import os
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from typing import Optional, Tuple

# Try to import database, fall back to in-memory storage
try:
    from core.database import get_connection
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# In-memory user storage (fallback when database not available)
_users = {}


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hash a password with salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return hashed.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against stored hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def create_user(username: str, password: str, is_admin: bool = False) -> bool:
    """Create a new user."""
    password_hash, salt = hash_password(password)
    stored_hash = f"{salt}:{password_hash}"

    if DATABASE_AVAILABLE:
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash, is_admin)
                    VALUES (?, ?, ?)
                ''', (username, stored_hash, 1 if is_admin else 0))
            return True
        except Exception:
            return False
    else:
        if username in _users:
            return False
        _users[username] = {
            'password_hash': stored_hash,
            'is_admin': is_admin
        }
        return True


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user and return user info if successful."""
    if DATABASE_AVAILABLE:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash, is_admin
                FROM users WHERE username = ?
            ''', (username,))
            row = cursor.fetchone()
            if row:
                stored_hash = row['password_hash']
                salt, hash_part = stored_hash.split(':')
                if verify_password(password, hash_part, salt):
                    return {
                        'id': row['id'],
                        'username': row['username'],
                        'is_admin': bool(row['is_admin'])
                    }
    else:
        user = _users.get(username)
        if user:
            stored_hash = user['password_hash']
            salt, hash_part = stored_hash.split(':')
            if verify_password(password, hash_part, salt):
                return {
                    'id': username,
                    'username': username,
                    'is_admin': user['is_admin']
                }
    return None


def get_user_count() -> int:
    """Get total number of users."""
    if DATABASE_AVAILABLE:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM users')
            return cursor.fetchone()['count']
    return len(_users)


def login_required(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if auth is enabled
        if not os.environ.get('AUTH_ENABLED', 'false').lower() == 'true':
            return f(*args, **kwargs)

        if 'user_id' not in session:
            # For API routes, return 401
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            # For page routes, redirect to login
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if auth is enabled
        if not os.environ.get('AUTH_ENABLED', 'false').lower() == 'true':
            return f(*args, **kwargs)

        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login_page'))

        if not session.get('is_admin'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function


def init_default_admin():
    """Create default admin user if no users exist."""
    if get_user_count() == 0:
        default_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        create_user('admin', default_password, is_admin=True)
        print(f"Created default admin user (username: admin)")
