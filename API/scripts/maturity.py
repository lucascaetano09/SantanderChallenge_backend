import sqlite3
import os
import math
from datetime import datetime

# Construct an absolute path to the database file.
# This goes up two directories from `scripts` to the project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'banco.db')

def get_db_connection():
    """Establishes and returns a connection with the database."""
    conn = sqlite3.connect(DB_PATH)
    # Using row_factory to easily access columns by name
    conn.row_factory = sqlite3.Row
    return conn

def get_maturity_overview():
    """
    Queries the MATURIDADE table to get the count of companies for each maturity stage.
    Returns a single object with maturity stages as keys and their counts as values.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT MATU, COUNT(DISTINCT ID) as count
        FROM MATURIDADE
        GROUP BY MATU
    """
    cur.execute(query)

    overview_data = {row['MATU']: row['count'] for row in cur.fetchall()}
    conn.close()
    return overview_data

def get_maturity_list(state=None, page=1):
    """
    Fetches a paginated list of companies, optionally filtered by maturity state.
    For each company, only the most recent entry based on DT_REFE is returned.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    params = []
    from_clause = "FROM ID"

    # If a state filter is provided, we create a subquery to get the relevant IDs.
    # This subquery is then used in the main query's WHERE clause.
    if state:
        from_clause += " WHERE ID IN (SELECT ID FROM MATURIDADE WHERE MATU = ?)"
        params.append(state)

    # This CTE (Common Table Expression) ensures we only work with the most recent
    # record for each unique ID, based on the latest DT_REFE.
    base_query_cte = f"""
        WITH LatestRecords AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY ID ORDER BY DT_REFE DESC) as rn
            {from_clause}
        )
        SELECT * FROM LatestRecords WHERE rn = 1
    """

    # --- Get total count for pagination ---
    count_query = f"SELECT COUNT(*) as total FROM ({base_query_cte})"
    cur.execute(count_query, tuple(params))
    total_items = cur.fetchone()['total']

    if total_items == 0:
        conn.close()
        return {"totalPages": 0, "accounts": []}

    # --- Pagination logic ---
    items_per_page = 20
    total_pages = math.ceil(total_items / items_per_page)
    offset = (page - 1) * items_per_page

    # --- Get paginated accounts ---
    select_query = f"""
        SELECT ID, VL_FATU, VL_SLDO, DT_ABRT, DS_CNAE, DT_REFE
        FROM ({base_query_cte})
        ORDER BY ID
        LIMIT ? OFFSET ?
    """

    # Add pagination params to the list for the final query
    paged_params = params + [items_per_page, offset]
    cur.execute(select_query, tuple(paged_params))

    processed_accounts = []
    for row in cur.fetchall():
        # Format the dates and currency values as requested
        opening_date = datetime.strptime(row['DT_ABRT'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        ref_date = datetime.strptime(row['DT_REFE'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

        processed_accounts.append({
            "ID": row['ID'],
            "FATURAMENTO": f"R${row['VL_FATU']}",
            "SALDO": f"R${row['VL_SLDO']}",
            "DATA_ABERTURA": opening_date,
            "CNAE": row['DS_CNAE'],
            "DATA_REFERENCIA": ref_date
        })

    conn.close()
    return {
        "totalPages": total_pages,
        "accounts": processed_accounts
    }