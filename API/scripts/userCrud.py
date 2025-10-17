import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Construct an absolute path to the database file.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'banco.db')
SQL_FILE_PATH = os.path.join(PROJECT_ROOT, 'definition.sql')

def _init_db_if_needed(conn):
    """
    Internal function to check for the USERS table and create it from definition.sql if it doesn't exist.
    """
    cur = conn.cursor()
    # Check if the USERS table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='USERS'")
    if cur.fetchone() is None:
        print("USERS table not found. Initializing database from definition.sql...")
        try:
            with open(SQL_FILE_PATH, 'r') as sql_file:
                sql_script = sql_file.read()
            cur.executescript(sql_script)
            conn.commit()
            print("Database initialized successfully.")
        except FileNotFoundError:
            print(f"ERROR: Could not find the database definition file at {SQL_FILE_PATH}")
            raise

def get_db_connection():
    """Establishes and returns a connection with the database."""
    conn = sqlite3.connect(DB_PATH)
    # Ensure the table exists before proceeding
    _init_db_if_needed(conn)
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