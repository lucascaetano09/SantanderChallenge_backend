from flask import Flask, jsonify, request
from flask_cors import CORS
from scripts import transactions, cnae, chat
from datetime import datetime

app = Flask(__name__)

# Define allowed origins for local development.
# Using a wildcard "*" with `supports_credentials=True` is not allowed by browsers.
# Instead, we list common local development server origins.
local_origins = [
    "http://localhost:3000",  # React
    "http://127.0.0.1:5500",  # VS Code Live Server
]
CORS(app, resources={r"/*": {"origins": local_origins, "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}}, supports_credentials=True) # Covers /transactions/* and /cnae/*


# Preserve the order of keys in JSON responses
app.json.sort_keys = False

# Instantiate the chat agent globally
chat_agent = chat.ChatAgentSimples()

@app.route('/transactions/overview', methods=['GET'])
def transactions_overview():
    """Endpoint to get an overview for a specific client."""
    id = request.args.get('id')
    if not id:
        return jsonify({'error': 'O parâmetro "id" do cliente é obrigatório'}), 400
    data = transactions.get_transactions_overview(id)
    return jsonify(data)

@app.route('/transactions/list', methods=['GET'])
def transactions_list():
    """Endpoint to get information for a specific client."""
    id = request.args.get('id')
    if not id:
        return jsonify({'error': 'O parâmetro "id" do cliente é obrigatório'}), 400

    # Get filter parameters from request
    date_str = request.args.get('date')
    date = [int(m) for m in date_str.split(',')] if date_str else None
    type_str = request.args.get('type')
    type = type_str.split(',') if type_str else None
    inOut = request.args.get('inOut', type=int)
    customProv = request.args.get('customProv')
    page = request.args.get('page', 1, type=int)

    data = transactions.get_transactions_list(id, date=date, type=type, inOut=inOut, customProv=customProv, page=page)
    if data is None:
        return jsonify({'error': 'Cliente não encontrado'}), 404
    return jsonify(data)

@app.route('/transactions/graphs/barChart', methods=['GET'])
def transactions_bar_chart():
    """Endpoint to get monthly income/expense data for a bar chart."""
    id = request.args.get('id')
    if not id:
        return jsonify({'error': 'O parâmetro "id" do cliente é obrigatório'}), 400
    data = transactions.get_transactions_barChart(id)
    return jsonify(data)

@app.route('/cnae/graphs/pieChart', methods=['GET'])
def cnae_pie_chart():
    """Endpoint to get data for a CNAE pie chart."""
    data = cnae.get_cnae_pieChart()
    return jsonify(data)

@app.route('/cnae/list', methods=['GET'])
def cnae_list():
    """Endpoint to get a paginated list of accounts for a specific CNAE."""
    cnae_param = request.args.get('cnae')
    if not cnae_param:
        return jsonify({'error': 'O parâmetro "cnae" é obrigatório'}), 400

    page = request.args.get('page', 1, type=int)

    data = cnae.get_cnae_list(cnae=cnae_param, page=page)
    return jsonify(data)


# --- CHATBOT API ENDPOINTS ---

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """Endpoint principal para chat"""
    try:
        data = request.json
        pergunta = data.get('pergunta', '').strip()
        
        if not pergunta:
            return jsonify({
                'success': False,
                'error': 'Pergunta é obrigatória'
            }), 400
        
        # Processar pergunta
        resposta = chat_agent.perguntar_ia(pergunta)
        
        return jsonify({
            'success': True,
            'pergunta': pergunta,
            'resposta': resposta,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/atualizar-dados', methods=['POST'])
def atualizar_dados():
    """Atualiza dados da tela atual (quando usuário muda filtros, página, etc.)"""
    try:
        data = request.json
        novos_dados = data.get('dados', {})
        
        success = chat_agent.atualizar_dados_tela(novos_dados)
        
        return jsonify({
            'success': success,
            'message': 'Dados atualizados com sucesso!',
            'dados_atuais': chat_agent.current_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Verifica status da API e dados atuais do chat"""
    return jsonify({
        'success': True,
        'status': 'API funcionando',
        'dados_atuais': chat_agent.current_data,
        'total_conversas': len(chat_agent.conversation_history),
        'ultima_atualizacao': datetime.now().isoformat()
    })

@app.route('/api/historico', methods=['GET'])
def historico():
    """Retorna histórico das conversas do chat"""
    return jsonify({
        'success': True,
        'historico': chat_agent.conversation_history[-10:],  # Últimas 10
        'total': len(chat_agent.conversation_history)
    })

@app.route('/api/limpar-historico', methods=['POST'])
def limpar_historico():
    """Limpa histórico de conversas do chat"""
    chat_agent.conversation_history = []
    return jsonify({
        'success': True,
        'message': 'Histórico limpo com sucesso!'
    })

@app.route('/api/configurar-sistema', methods=['POST'])
def configurar_sistema():
    """Permite alterar informações do sistema do chat dinamicamente"""
    try:
        data = request.json
        if 'site_info' in data:
            chat_agent.site_info = data['site_info']
        if 'current_data' in data:
            chat_agent.current_data = data['current_data']
        return jsonify({'success': True, 'message': 'Sistema configurado com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
