import sqlite3

# Função para consultar dados do cliente

def consultar_cliente(cnpj, db_path='banco.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Buscar dados do cliente
    cursor.execute("SELECT ID, VL_FATU FROM ID WHERE ID = ?", (cnpj,))
    cliente = cursor.fetchone()
    if not cliente:
        print(f"Cliente {cnpj} não encontrado.")
        return
    faturamento = cliente[1]

    # Buscar todas as transações vinculadas ao cliente (pagador ou recebedor)
    cursor.execute("""
        SELECT VL, DS_TRAN, DT_REFE, ID_PGTO, ID_RCBE
        FROM TRANSACOES
        WHERE ID_PGTO = ? OR ID_RCBE = ?
    """, (cnpj, cnpj))
    transacoes = cursor.fetchall()

    # Calcular quantidade e valor total
    qtd_transacoes = len(transacoes)
    valor_total = sum([t[0] for t in transacoes])

    print(f"Cliente: {cnpj}")py
    print(f"Faturamento anual: {faturamento}")
    print(f"Quantidade de transações: {qtd_transacoes}")
    print(f"Valor total transacionado: {valor_total}")
    print("Transações:")
    for t in transacoes:
        print(f"  Valor: {t[0]}, Descrição: {t[1]}, Data: {t[2]}, Pagador: {t[3]}, Recebedor: {t[4]}")

    conn.close()

if __name__ == "__main__":
    cnpj = input("Digite o CNPJ/ID do cliente: ")
    consultar_cliente(cnpj)
