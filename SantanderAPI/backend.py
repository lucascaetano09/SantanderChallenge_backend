from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
DB_PATH = 'banco.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/stats', methods=['GET'])
def stats():
    conn = get_db()
    cur = conn.cursor()
    # Total de clientes
    cur.execute('SELECT COUNT(*) as total FROM ID')
    total_clientes = cur.fetchone()['total']
    # Total de transações
    cur.execute('SELECT COUNT(*) as total FROM TRANSACOES')
    total_transacoes = cur.fetchone()['total']
    # Valor total transacionado
    cur.execute('SELECT SUM(VL) as total FROM TRANSACOES')
    valor_total = cur.fetchone()['total'] or 0
    # Faturamento total
    cur.execute('SELECT SUM(VL_FATU) as total FROM ID')
    faturamento_total = cur.fetchone()['total'] or 0
    conn.close()
    return jsonify({
        'totalClientes': total_clientes,
        'totalTransacoes': total_transacoes,
        'valorTotalTransacoes': valor_total,
        'faturamentoTotal': faturamento_total
    })

@app.route('/api/cliente/<id>', methods=['GET'])
def cliente_info(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM ID WHERE ID = ?', (id,))
    cliente = cur.fetchone()
    if not cliente:
        conn.close()
        return jsonify({'error': 'Cliente não encontrado'}), 404
    # Transações vinculadas
    cur.execute('''SELECT * FROM TRANSACOES WHERE ID_PGTO = ? OR ID_RCBE = ? ORDER BY DT_REFE DESC''', (id, id))
    transacoes = [dict(row) for row in cur.fetchall()]
    valor_total = sum([t['VL'] for t in transacoes])
    conn.close()
    return jsonify({
        'id': cliente['ID'],
        'faturamento': cliente['VL_FATU'],
        'qtdTransacoes': len(transacoes),
        'valorTotalTransacionado': valor_total,
        'transacoes': transacoes
    })

@app.route('/api/transacoes', methods=['GET'])
def ultimas_transacoes():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM TRANSACOES ORDER BY DT_REFE DESC LIMIT 20')
    transacoes = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({'transacoes': transacoes})

@app.route('/api/clientes', methods=['GET'])
def clientes():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT ID, DS_CNAE, VL_FATU, VL_SLDO, DT_ABRT FROM ID')
    clientes = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(clientes)

if __name__ == '__main__':
    app.run(debug=True)
