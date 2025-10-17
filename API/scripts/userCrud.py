import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Construct an absolute path to the database file.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'banco.db')

def get_db_connection():
    """Establishes and returns a connection with the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def register_user(login, password):
    """
    Registers a new user by hashing their password and storing it in the USERS table.
    Returns a dictionary indicating success or failure.
    """
    if not login or not password:
        return {'success': False, 'error': 'Login e senha são obrigatórios.'}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if user already exists
    cur.execute("SELECT login FROM USERS WHERE login = ?", (login,))
    if cur.fetchone():
        conn.close()
        return {'success': False, 'error': 'Usuário já existe.'}, 409 # 409 Conflict

    # Hash the password and insert the new user
    hashed_password = generate_password_hash(password)
    try:
        cur.execute("INSERT INTO USERS (login, pwd) VALUES (?, ?)", (login, hashed_password))
        conn.commit()
        conn.close()
        return {'success': True, 'message': 'Usuário registrado com sucesso.'}, 201 # 201 Created
    except Exception as e:
        conn.rollback()
        conn.close()
        return {'success': False, 'error': str(e)}, 500

def verify_user(login, password):
    """
    Verifies a user's credentials by comparing the provided password with the stored hash.
    Returns a dictionary indicating success or failure.
    """
    if not login or not password:
        return {'success': False, 'error': 'Login e senha são obrigatórios.'}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT pwd FROM USERS WHERE login = ?", (login,))
    user_row = cur.fetchone()
    conn.close()

    if user_row and check_password_hash(user_row['pwd'], password):
        return {'success': True, 'message': 'Login bem-sucedido.'}, 200
    else:
        return {'success': False, 'error': 'Credenciais inválidas.'}, 401 # 401 Unauthorized