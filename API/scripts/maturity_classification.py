import sqlite3
import os
import pandas as pd
import numpy as np
from datetime import datetime

# --- Configuração do Banco de Dados ---
# Constrói o caminho absoluto para o arquivo do banco de dados.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'banco.db')

def get_db_connection():
    """Estabelece e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    return conn

# --- 1. Carregamento dos Dados ---
def load_data(conn):
    """
    Carrega os dados das tabelas 'ID' e 'TRANSACOES' para DataFrames do pandas.
    
    Args:
        conn: Objeto de conexão com o banco de dados.
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: DataFrames para clientes e transações.
    """
    print("Carregando dados das tabelas 'ID' e 'TRANSACOES'...")
    id_df = pd.read_sql_query("SELECT * FROM ID", conn)
    transactions_df = pd.read_sql_query("SELECT * FROM TRANSACOES", conn)
    print("Dados carregados com sucesso.")
    return id_df, transactions_df

# --- 2. Engenharia de Features ---
def _calculate_balance_trend(group):
    """
    Calcula a inclinação (slope) da tendência de saldo para um grupo de registros de uma empresa.
    Utiliza regressão linear sobre os valores de saldo e as datas de referência.
    """
    # Garante a ordem cronológica
    group = group.sort_values('DT_REFE')
    # Converte datas para um formato numérico (ordinal) para a regressão
    X = group['DT_REFE'].apply(lambda d: pd.to_datetime(d).toordinal()).values
    y = group['VL_SLDO'].values
    
    # Evita erro se houver menos de 2 pontos de dados
    if len(X) < 2:
        return 0.0
        
    # Calcula a regressão linear (grau 1) e retorna a inclinação (slope)
    slope, _ = np.polyfit(X, y, 1)
    return slope

def _calculate_net_cash_flow(transactions_df):
    """Calcula o fluxo de caixa líquido para cada empresa a partir das transações."""
    # Soma de todas as receitas por empresa
    income = transactions_df.groupby('ID_RCBE')['VL'].sum().rename('INCOME')
    # Soma de todas as despesas por empresa
    expenses = transactions_df.groupby('ID_PGTO')['VL'].sum().rename('EXPENSES')
    
    # Combina receitas e despesas em um único DataFrame
    cash_flow = pd.concat([income, expenses], axis=1).fillna(0)
    cash_flow['FLUXO_CAIXA_LIQUIDO_3M'] = cash_flow['INCOME'] - cash_flow['EXPENSES']
    
    return cash_flow[['FLUXO_CAIXA_LIQUIDO_3M']]

def calculate_features(id_df, transactions_df):
    """
    Calcula todas as métricas (features) necessárias para a classificação de maturidade.
    
    Args:
        id_df (pd.DataFrame): DataFrame com os dados dos clientes.
        transactions_df (pd.DataFrame): DataFrame com os dados das transações.
        
    Returns:
        pd.DataFrame: DataFrame com o ID de cada empresa e suas features calculadas.
    """
    print("Iniciando engenharia de features...")
    
    # Agrupa por ID para obter dados únicos por empresa
    # 'first()' é usado para pegar os valores que são constantes por ID (DT_ABRT, VL_FATU)
    features_df = id_df.groupby('ID').agg(
        DT_ABRT=('DT_ABRT', 'first'),
        FATURAMENTO_ANUAL=('VL_FATU', 'first')
    ).reset_index()

    # 1. IDADE_ANOS
    current_date = datetime.now()
    features_df['IDADE_ANOS'] = (current_date - pd.to_datetime(features_df['DT_ABRT'])).dt.days / 365.25

    # 2. TENDENCIA_SALDO
    print("Calculando tendência de saldo...")
    balance_trend = id_df.groupby('ID').apply(_calculate_balance_trend).rename('TENDENCIA_SALDO')
    features_df = features_df.merge(balance_trend, on='ID')

    # 3. FLUXO_CAIXA_LIQUIDO_3M
    print("Calculando fluxo de caixa líquido...")
    net_cash_flow = _calculate_net_cash_flow(transactions_df)
    features_df = features_df.merge(net_cash_flow, left_on='ID', right_index=True, how='left').fillna(0)

    print("Features calculadas com sucesso.")
    return features_df

# --- 3. Lógica de Classificação ---
def _classify_maturity(row):
    """Aplica as regras de negócio para classificar uma única empresa."""
    # Regra 1: Iniciante
    if row['IDADE_ANOS'] < 2:
        return 'Iniciante'
    
    # Regra 2: Declínio
    # Limiar de fluxo de caixa negativo: -10% do faturamento mensal
    monthly_revenue = row['FATURAMENTO_ANUAL'] / 12
    negative_cash_flow_threshold = -0.10 * monthly_revenue if monthly_revenue > 0 else 0
    
    if row['TENDENCIA_SALDO'] < -0.1 or row['FLUXO_CAIXA_LIQUIDO_3M'] < negative_cash_flow_threshold:
        return 'Declínio'
        
    # Regra 3: Expansão (não pode ser 'Iniciante', já coberto pela primeira regra)
    if row['TENDENCIA_SALDO'] > 0.1 and row['FLUXO_CAIXA_LIQUIDO_3M'] > 0:
        return 'Expansão'
        
    # Regra 4: Madura (caso padrão)
    return 'Madura'

def classify_companies(features_df):
    """
    Classifica todas as empresas com base em suas features.
    
    Args:
        features_df (pd.DataFrame): DataFrame com as features das empresas.
        
    Returns:
        pd.DataFrame: DataFrame com as colunas 'ID' e 'MATU' (maturidade).
    """
    print("Classificando empresas...")
    features_df['MATU'] = features_df.apply(_classify_maturity, axis=1)
    print("Classificação concluída.")
    return features_df[['ID', 'MATU']]

# --- 4. Salvando os Resultados ---
def save_results(conn, maturity_df):
    """
    Cria a tabela 'MATURIDADE' (se não existir) e insere os resultados da classificação.
    
    Args:
        conn: Objeto de conexão com o banco de dados.
        maturity_df (pd.DataFrame): DataFrame com os resultados da classificação.
    """
    print("Salvando resultados no banco de dados...")
    cursor = conn.cursor()
    
    # Cria a tabela se ela não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MATURIDADE (
            ID TEXT PRIMARY KEY,
            MATU TEXT NOT NULL,
            FOREIGN KEY (ID) REFERENCES ID(ID)
        )
    """)
    
    # Insere os dados na tabela, substituindo registros existentes para o mesmo ID
    maturity_df.to_sql('MATURIDADE', conn, if_exists='replace', index=False)
    
    conn.commit()
    print(f"{len(maturity_df)} registros salvos na tabela 'MATURIDADE'.")


# --- Função Principal ---
def run_maturity_analysis():
    """
    Orquestra todo o processo de análise de maturidade:
    1. Conecta ao banco de dados.
    2. Carrega os dados.
    3. Calcula as features.
    4. Classifica as empresas.
    5. Salva os resultados.
    """
    conn = None
    try:
        conn = get_db_connection()
        
        # Passos do processo
        id_data, transactions_data = load_data(conn)
        features = calculate_features(id_data, transactions_data)
        maturity_results = classify_companies(features)
        save_results(conn, maturity_results)
        
        print("\nAnálise de maturidade concluída com sucesso!")
        
    except Exception as e:
        print(f"Ocorreu um erro durante a análise: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == '__main__':
    run_maturity_analysis()