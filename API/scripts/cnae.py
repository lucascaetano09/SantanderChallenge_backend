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

def get_cnae_pieChart():
    """
    Fetches data for a pie chart of the top 5 CNAEs by total faturamento.
    """
    conn = get_db()
    cur = conn.cursor()

    # This query performs the following steps:
    # 1. `RankedFaturamento`: Ranks each record within its CNAE group by `VL_FATU` descending.
    # 2. `top100Sum`: For each CNAE, calculates the sum of `VL_FATU` for only the top 10 ranked records.
    # 3. `CnaeAccountCounts`: Counts the total number of accounts for each CNAE.
    # 4. The final `SELECT` joins these results, orders the CNAEs by the `top100_VL_FATU_Sum` to find the top 5,
    #    and returns the CNAE description and its total account count.
    query = """
        WITH RankedFaturamento AS (
            SELECT
                DS_CNAE,
                VL_FATU,
                ROW_NUMBER() OVER(PARTITION BY DS_CNAE ORDER BY VL_FATU DESC) as rn
            FROM ID
        ),
        top100Sum AS (
            SELECT
                DS_CNAE,
                SUM(VL_FATU) as top100_VL_FATU_Sum
            FROM RankedFaturamento
            WHERE rn <= 100
            GROUP BY DS_CNAE
        ),
        CnaeAccountCounts AS (
            SELECT
                DS_CNAE,
                COUNT(ID) as accounts
            FROM ID
            GROUP BY DS_CNAE
        )
        SELECT T.DS_CNAE as cnae, C.accounts
        FROM top100Sum T
        JOIN CnaeAccountCounts C ON T.DS_CNAE = C.DS_CNAE
        ORDER BY T.top100_VL_FATU_Sum DESC
        LIMIT 5;
    """
    cur.execute(query)

    pie_chart_data = [dict(row) for row in cur.fetchall()]
    conn.close()

    # Sort the list of 5 objects by the 'accounts' count in descending order
    sorted_pie_chart_data = sorted(pie_chart_data, key=lambda x: x['accounts'], reverse=True)

    return sorted_pie_chart_data

def get_cnae_list(cnae, page=1):
    """
    Fetches a paginated list of accounts for a given CNAE.
    For each account, only the most recent entry based on DT_REFE is considered.
    """
    conn = get_db()
    cur = conn.cursor()

    # This CTE identifies the most recent row for each ID within the specified CNAE
    base_query_cte = """
        FROM ID
        WHERE (ID, DT_REFE) IN (
            SELECT ID, MAX(DT_REFE)
            FROM ID
            WHERE DS_CNAE = ?
            GROUP BY ID
        )
    """

    # --- Get total count for pagination ---
    count_query = f"SELECT COUNT(*) as total {base_query_cte}"
    cur.execute(count_query, (cnae,))
    total_items = cur.fetchone()['total']

    if total_items == 0:
        conn.close()
        return {"totalPages": 0, "accounts": []}

    # Pagination logic
    items_per_page = 12
    total_pages = math.ceil(total_items / items_per_page)
    offset = (page - 1) * items_per_page

    # --- Get paginated accounts ---
    select_query = f"""
        SELECT ID, VL_FATU, DT_ABRT
        {base_query_cte}
        ORDER BY ID
        LIMIT ? OFFSET ?
    """

    cur.execute(select_query, (cnae, items_per_page, offset))

    processed_accounts = []
    for row in cur.fetchall():
        # Format the opening date
        opening_date = datetime.strptime(row['DT_ABRT'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

        processed_accounts.append({
            "account": row['ID'],
            "invoicing": f"R${row['VL_FATU']}",
            "date": opening_date
        })

    conn.close()
    return {
        "totalPages": total_pages,
        "accounts": processed_accounts
    }