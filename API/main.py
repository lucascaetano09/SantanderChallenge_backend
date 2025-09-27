from flask import Flask, jsonify, request
from flask_cors import CORS
from scripts import transactions, cnae

app = Flask(__name__)

# Configure CORS to be more specific and robust.
# This allows requests from any origin, with common methods and headers,
# and supports credentials, which is a common requirement for web apps.
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}}, supports_credentials=True)


# Preserve the order of keys in JSON responses
app.json.sort_keys = False

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

if __name__ == '__main__':
    app.run(debug=True)
