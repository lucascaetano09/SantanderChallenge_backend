import sqlite3
import os
import math
from datetime import datetime

# Construct an absolute path to the database file.
# This goes up two directories from `scripts` to the project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'banco.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_transactions_overview(id):
    """Fetches statistics for a specific client from the database."""
    conn = get_db()
    cur = conn.cursor()
    # Total de clientes que pagaram para o ID consultado
    cur.execute('SELECT COUNT(DISTINCT ID_PGTO) as total FROM TRANSACOES WHERE ID_RCBE = ?', (id,))
    total_clientes = cur.fetchone()['total'] or 0

    # Total de transações (pago e recebido)
    cur.execute('SELECT COUNT(*) as total FROM TRANSACOES WHERE ID_PGTO = ? OR ID_RCBE = ?', (id, id))
    total_transacoes = cur.fetchone()['total'] or 0

    # Saldo das transações (receitas - despesas)
    query = '''
        SELECT SUM(CASE WHEN ID_RCBE = ? THEN VL WHEN ID_PGTO = ? THEN -VL ELSE 0 END) as balance
        FROM TRANSACOES WHERE ID_PGTO = ? OR ID_RCBE = ?
    '''
    cur.execute(query, (id, id, id, id))
    transaction_balance = cur.fetchone()['balance'] or 0

    conn.close()
    return {
        'totalClientes': total_clientes, # Clientes que pagaram para o ID
        'totalTransacoes': total_transacoes, # Transações do ID
        'transactionBalance': transaction_balance # Saldo do ID
    }

def get_transactions_list(id, date=None, type=None, inOut=None, customProv=None, page=1):
    """Fetches a specific account's information and transactions."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM ID WHERE ID = ?', (id,))
    cliente = cur.fetchone()
    if not cliente:
        conn.close()
        return None

    # Build dynamic query for transactions
    where_clauses = []
    params = []

    # inOut filter
    if inOut == 1: # Income
        where_clauses.append("ID_RCBE = ?")
        params.append(id)
    elif inOut == 2: # Expense
        where_clauses.append("ID_PGTO = ?")
        params.append(id)
    else: # Both
        where_clauses.append("(ID_PGTO = ? OR ID_RCBE = ?)")
        params.extend([id, id])

    # date filter (months)
    if date:
        placeholders = ','.join('?' for _ in date)
        where_clauses.append(f"STRFTIME('%m', DT_REFE) IN ({placeholders})")
        params.extend(map(str, date))

    # type filter (transaction description)
    if type:
        placeholders = ','.join('?' for _ in type)
        where_clauses.append(f"DS_TRAN IN ({placeholders})")
        params.extend(type)

    # customProv filter (customer or provider)
    if customProv:
        where_clauses.append("(ID_PGTO = ? OR ID_RCBE = ?)")
        params.extend([customProv, customProv])

    # --- Get total count for pagination ---
    count_query = f"SELECT COUNT(*) as total FROM TRANSACOES WHERE {' AND '.join(where_clauses)}"
    cur.execute(count_query, tuple(params))
    total_items = cur.fetchone()['total']

    # Pagination logic
    items_per_page = 20
    total_pages = math.ceil(total_items / items_per_page)
    offset = (page - 1) * items_per_page

    # --- Get paginated transactions ---
    select_query = f"SELECT * FROM TRANSACOES WHERE {' AND '.join(where_clauses)} ORDER BY DT_REFE DESC LIMIT ? OFFSET ?"
    
    # Add pagination params to the list for the final query
    paged_params = params + [items_per_page, offset]

    cur.execute(select_query, tuple(paged_params))
    
    processed_transactions = []
    for row in cur.fetchall():
        transaction_date = datetime.strptime(row['DT_REFE'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

        if row['ID_PGTO'] == id:
            in_out_status = "Saída"
            customer_provider = row['ID_RCBE']
        else:
            in_out_status = "Entrada"
            customer_provider = row['ID_PGTO']

        processed_transactions.append({
            "inOut": in_out_status,
            "customProv": customer_provider,
            "date": transaction_date,
            "type": row['DS_TRAN'],
            "value": f"R${row['VL']}"
        })

    conn.close()
    return {
        "totalPages": total_pages,
        "transactions": processed_transactions
    }

def get_transactions_barChart(id):
    """Fetches monthly income and expense data for a bar chart."""
    conn = get_db()
    cur = conn.cursor()

    # A mapping of month numbers to abbreviated Portuguese names.
    month_map = {
        '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr', '05': 'Mai', '06': 'Jun',
        '07': 'Jul', '08': 'Ago', '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
    }

    query = """
        SELECT
            STRFTIME('%m', DT_REFE) as month_num,
            SUM(CASE WHEN ID_RCBE = ? THEN VL ELSE 0 END) as income,
            SUM(CASE WHEN ID_PGTO = ? THEN VL ELSE 0 END) as expense
        FROM TRANSACOES
        WHERE ID_PGTO = ? OR ID_RCBE = ?
        GROUP BY month_num
        ORDER BY month_num;
    """
    cur.execute(query, (id, id, id, id))
    
    chart_data = []
    for row in cur.fetchall():
        chart_data.append({
            "month": month_map.get(row['month_num'], 'Unk'),
            "income": row['income'],
            "expense": row['expense']
        })

    conn.close()
    return chart_data
