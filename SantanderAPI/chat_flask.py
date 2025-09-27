# app.py - API Flask para Chat Agent
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import openai
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permite chamadas do frontend

class ChatAgentSimples:
    def __init__(self):
        # SUA API KEY
        self.client = openai.OpenAI(
            api_key=""
        )
        
        self.conversation_history = []
        
        # CONFIGURE AQUI O QUE SUA IA DEVE SABER SOBRE O SITE/SISTEMA
        self.site_info = """
🏢 INFORMAÇÕES DO SISTEMA/SITE:

NOME DO SISTEMA: Dashboard Santander BI
DESCRIÇÃO: Sistema de análise de dados e relatórios para o banco Santander

FUNCIONALIDADES PRINCIPAIS:
- Dashboards de vendas e performance
- Relatórios financeiros em tempo real  
- Análise de clientes e produtos
- Gráficos interativos de métricas
- Filtros por período, região, produto

COMO NAVEGAR:
- Menu principal no topo da página
- Sidebar esquerda com categorias (Vendas, Financeiro, Clientes)
- Filtros no canto superior direito
- Gráficos clicáveis para drill-down
- Exportar relatórios no botão "Download"

DADOS DISPONÍVEIS:
- Vendas por período (diário, mensal, anual)
- Performance por região (Norte, Sul, Sudeste, Nordeste, Centro-Oeste)
- Top produtos mais vendidos
- Análise de clientes (novos vs recorrentes)
- Métricas financeiras (receita, margem, lucro)
- KPIs principais (conversão, ticket médio, satisfação)

FILTROS DISPONÍVEIS:
- Período: Hoje, Última semana, Último mês, Trimestre, Ano
- Região: Todas, Norte, Sul, Sudeste, Nordeste, Centro-Oeste
- Produto: Todos, Conta Corrente, Cartão de Crédito, Empréstimos, Investimentos
- Canal: Agência, Internet Banking, App Mobile, ATM

PROBLEMAS COMUNS E SOLUÇÕES:
- Dados não carregam: Verificar filtros aplicados
- Gráfico vazio: Selecionar período com dados
- Lentidão: Reduzir intervalo de tempo do filtro
- Erro de acesso: Verificar permissões com administrador

CONTATOS DE SUPORTE:
- TI: ti@santander.com.br
- BI: bi-suporte@santander.com.br  
- Telefone: (11) 4004-3535
"""

        # DADOS ATUAIS DO SISTEMA (atualize conforme necessário)
        self.current_data = {
            "data_atual": "15/01/2024",
            "usuario_logado": "Analista",
            "tela_atual": "Dashboard Principal",
            "filtros_ativos": {
                "periodo": "Último mês",
                "regiao": "Todas",
                "produto": "Todos"
            },
            "metricas_visiveis": {
                "receita_total": "R$ 2.8M",
                "vendas": "12.450",
                "crescimento": "+15.3%",
                "clientes_ativos": "45.230",
                "ticket_medio": "R$ 225",
                "satisfacao": "4.2/5"
            },
            "alertas": [
                "Meta de vendas atingida em 110%",
                "Região Norte com baixa performance",
                "Novo produto de investimento disponível"
            ]
        }

    def perguntar_ia(self, pergunta_usuario):
        """Processa pergunta do usuário"""
        
        # Contexto completo que a IA conhece
        contexto_completo = f"""
{self.site_info}

DADOS ATUAIS NA TELA:
{json.dumps(self.current_data, indent=2, ensure_ascii=False)}

HISTÓRICO DA CONVERSA:
{self._formatar_historico()}
"""

        system_prompt = """Você é a assistente virtual do Dashboard Santander BI.

SUA PERSONALIDADE:
- Amigável e prestativa (como atendente do banco)
- Responde de forma simples e clara
- Sempre tenta ajudar o usuário
- Usa informações específicas do sistema
- Quando não souber algo, admite e oferece alternativas

SUAS RESPONSABILIDADES:
- Explicar funcionalidades do dashboard
- Ajudar com navegação e filtros
- Explicar dados e métricas mostrados
- Dar dicas de uso do sistema
- Resolver problemas comuns
- Indicar contatos quando necessário

REGRAS:
- Sempre baseie respostas nas informações do sistema fornecidas
- Use dados específicos quando disponíveis
- Seja concisa (máximo 3 parágrafos)
- Se não souber algo específico, diga "Não tenho essa informação" e ofereça alternativa
- Sempre termine perguntando se precisa de mais ajuda

FORMATO DE RESPOSTA:
- Resposta direta à pergunta
- Informação adicional útil (se relevante)
- Pergunta se precisa de mais ajuda
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt + "\n\nCONTEXTO DO SISTEMA:\n" + contexto_completo},
                    {"role": "user", "content": pergunta_usuario}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            resposta = response.choices[0].message.content
            
            # Salvar no histórico
            self.conversation_history.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'usuario': pergunta_usuario,
                'assistente': resposta
            })
            
            return resposta
            
        except Exception as e:
            return f"Desculpe, ocorreu um erro técnico. Tente novamente em alguns segundos. Se persistir, entre em contato com o suporte TI: (11) 4004-3535"

    def _formatar_historico(self):
        """Formata histórico das últimas conversas"""
        if not self.conversation_history:
            return "Primeira conversa."
        
        historico = ""
        for item in self.conversation_history[-3:]:  # Últimas 3 interações
            historico += f"[{item['timestamp']}] Usuário: {item['usuario']}\n"
            historico += f"Assistente: {item['assistente']}\n\n"
        
        return historico

    def atualizar_dados_tela(self, novos_dados):
        """Atualiza dados da tela atual"""
        self.current_data.update(novos_dados)
        return True

# Instância global do chat agent
chat_agent = ChatAgentSimples()

# ROTAS DA API

@app.route('/', methods=['GET'])
def home():
    """Página de teste da API"""
    html_test = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Agent API - Teste</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .chat-container { border: 1px solid #ddd; border-radius: 10px; padding: 20px; }
        .messages { height: 400px; overflow-y: auto; border: 1px solid #eee; padding: 15px; margin: 10px 0; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; text-align: right; }
        .bot { background: #f1f8e9; }
        .input-area { display: flex; gap: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .suggestions { margin: 10px 0; }
        .suggestion-btn { margin: 5px; padding: 5px 10px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 3px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>🤖 Chat Agent API - Teste</h1>
    
    <div class="chat-container">
        <div id="messages" class="messages">
            <div class="message bot">Olá! Sou a assistente virtual do Santander BI. Como posso ajudar?</div>
        </div>
        
        <div class="suggestions">
            <strong>Sugestões:</strong><br>
            <button class="suggestion-btn" onclick="sendMessage('Como funciona o dashboard?')">Como funciona o dashboard?</button>
            <button class="suggestion-btn" onclick="sendMessage('Onde vejo relatórios?')">Onde vejo relatórios?</button>
            <button class="suggestion-btn" onclick="sendMessage('Como aplicar filtros?')">Como aplicar filtros?</button>
            <button class="suggestion-btn" onclick="sendMessage('Explique as métricas atuais')">Explique as métricas atuais</button>
        </div>
        
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Digite sua pergunta..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        async function sendMessage(text = null) {
            const input = document.getElementById('userInput');
            const message = text || input.value.trim();
            
            if (!message) return;
            
            // Adicionar mensagem do usuário
            addMessage(message, 'user');
            
            // Limpar input
            if (!text) input.value = '';
            
            try {
                // Chamar API
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({pergunta: message})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.resposta, 'bot');
                } else {
                    addMessage('Erro: ' + data.error, 'bot');
                }
                
            } catch (error) {
                addMessage('Erro de conexão. Tente novamente.', 'bot');
            }
        }
        
        function addMessage(text, sender) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${sender}`;
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
    </script>
</body>
</html>
    """
    return render_template_string(html_test)

@app.route('/api/chat', methods=['POST'])
def chat():
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
    """Verifica status da API e dados atuais"""
    return jsonify({
        'success': True,
        'status': 'API funcionando',
        'dados_atuais': chat_agent.current_data,
        'total_conversas': len(chat_agent.conversation_history),
        'ultima_atualizacao': datetime.now().isoformat()
    })

@app.route('/api/historico', methods=['GET'])
def historico():
    """Retorna histórico das conversas"""
    return jsonify({
        'success': True,
        'historico': chat_agent.conversation_history[-10:],  # Últimas 10
        'total': len(chat_agent.conversation_history)
    })

@app.route('/api/limpar-historico', methods=['POST'])
def limpar_historico():
    """Limpa histórico de conversas"""
    chat_agent.conversation_history = []
    return jsonify({
        'success': True,
        'message': 'Histórico limpo com sucesso!'
    })

@app.route('/api/configurar-sistema', methods=['POST'])
def configurar_sistema():
    """Permite alterar informações do sistema dinamicamente"""
    try:
        data = request.json
        
        if 'site_info' in data:
            chat_agent.site_info = data['site_info']
        
        if 'current_data' in data:
            chat_agent.current_data = data['current_data']
        
        return jsonify({
            'success': True,
            'message': 'Sistema configurado com sucesso!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# TRATAMENTO DE ERROS
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint não encontrado'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Erro interno do servidor'
    }), 500

if __name__ == '__main__':
    print("🚀 Iniciando Chat Agent API...")
    print("📋 Endpoints disponíveis:")
    print("  GET  / - Página de teste")
    print("  POST /api/chat - Chat principal")
    print("  POST /api/atualizar-dados - Atualizar dados da tela")
    print("  GET  /api/status - Status da API")
    print("  GET  /api/historico - Histórico de conversas")
    print("  POST /api/limpar-historico - Limpar histórico")
    print("  POST /api/configurar-sistema - Configurar sistema")
    print("-" * 50)
    print("🌐 Acesse: http://localhost:5000 para testar")
    print("🔗 API Base: http://localhost:5000/api/")
    
    app.run(debug=True, host='0.0.0.0', port=5000)