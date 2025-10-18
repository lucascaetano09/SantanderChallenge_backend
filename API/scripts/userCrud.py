import sqlite3
import os
import re
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
            with open(SQL_FILE_PATH, 'r', encoding='utf-8') as sql_file:
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

def _validate_email(email):
    """
    Valida o formato do email.
    """
    if not email or not isinstance(email, str):
        return False
    
    # Remove espaços em branco
    email = email.strip()
    
    # Verifica tamanho razoável
    if len(email) < 5 or len(email) > 254:  # RFC 5321
        return False
    
    # Regex básico para validar email (não pega 100% dos casos, mas é bom o suficiente)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False
    
    return True

def _validate_password(password):
    """
    Valida requisitos básicos de senha.
    """
    if not password or not isinstance(password, str):
        return False
    
    # Requisitos mínimos de senha
    if len(password) < 8:
        return False
    
    if len(password) > 128:  # Limite máximo razoável
        return False
    
    return True

def register_user(login, password):
    """
    Registers a new user by hashing their password and storing it in the USERS table.
    Returns a dictionary indicating success or failure.
    """
    # Validações de entrada
    if not login or not password:
        return {'success': False, 'error': 'Email e senha são obrigatórios.'}, 400
    
    # Remove espaços em branco e converte para minúsculo
    login = login.strip().lower()
    
    # Validação do formato do email
    if not _validate_email(login):
        return {'success': False, 'error': 'Email inválido.'}, 400
    
    # Validação da senha
    if not _validate_password(password):
        return {'success': False, 'error': 'Senha deve ter entre 8 e 128 caracteres.'}, 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if user already exists
        cur.execute("SELECT login FROM USERS WHERE login = ?", (login,))
        if cur.fetchone():
            return {'success': False, 'error': 'Email já cadastrado.'}, 409

        # Hash the password and insert the new user
        hashed_password = generate_password_hash(password, method='scrypt')
        cur.execute("INSERT INTO USERS (login, pwd) VALUES (?, ?)", (login, hashed_password))
        conn.commit()
        return {'success': True, 'message': 'Usuário registrado com sucesso.'}, 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        # Não expor detalhes do erro ao usuário em produção
        print(f"Erro ao registrar usuário: {e}")
        return {'success': False, 'error': 'Erro ao registrar usuário.'}, 500
        
    finally:
        if conn:
            conn.close()

def verify_user(login, password):
    """
    Verifies a user's credentials by comparing the provided password with the stored hash.
    Returns a dictionary indicating success or failure.
    """
    # Validações de entrada
    if not login or not password:
        return {'success': False, 'error': 'Email e senha são obrigatórios.'}, 400
    
    # Remove espaços em branco e converte para minúsculo
    login = login.strip().lower()
    
    # Validação básica
    if not _validate_email(login) or not _validate_password(password):
        return {'success': False, 'error': 'Credenciais inválidas.'}, 401

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Busca pelo email
        cur.execute("SELECT pwd FROM USERS WHERE login = ?", (login,))
        user_row = cur.fetchone()

        if user_row and check_password_hash(user_row['pwd'], password):
            return {'success': True, 'message': 'Login bem-sucedido.'}, 200
        else:
            # Mensagem genérica para não indicar se o email existe
            return {'success': False, 'error': 'Credenciais inválidas.'}, 401
            
    except Exception as e:
        print(f"Erro ao verificar usuário: {e}")
        return {'success': False, 'error': 'Erro ao processar login.'}, 500
        
    finally:
        if conn:
            conn.close()