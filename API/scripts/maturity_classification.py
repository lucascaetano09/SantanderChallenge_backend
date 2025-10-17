# maturity_classification.py

import sqlite3
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import warnings

# Suppress future warnings from scikit-learn for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)

DB_PATH = './banco.db'

def load_data(db_path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Connects to the SQLite database and loads the required tables.
    """
    print("Connecting to the database and loading tables...")
    try:
        with sqlite3.connect(db_path) as conn:
            df_id = pd.read_sql_query("SELECT * FROM ID", conn)
            df_transacoes = pd.read_sql_query("SELECT * FROM TRANSACOES", conn)
            df_maturidade = pd.read_sql_query("SELECT * FROM MATURIDADE", conn)
        print("Data loaded successfully.")
        return df_id, df_transacoes, df_maturidade
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def create_features(df_id: pd.DataFrame, df_transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Engineers features from raw data to represent company maturity.
    """
    print("Starting feature engineering...")
    df_id['DT_ABRT'] = pd.to_datetime(df_id['DT_ABRT'])
    df_transacoes['DT_REFE'] = pd.to_datetime(df_transacoes['DT_REFE'])

    # Use the most recent transaction date as the reference for age/recency calculations
    snapshot_date = df_transacoes['DT_REFE'].max()
    features_df = df_id.set_index('ID').copy()

    # Feature: Account Age
    features_df['idade_conta_dias'] = (snapshot_date - features_df['DT_ABRT']).dt.days

    # Features: Transactional behavior (as payer and receiver)
    pgto_agg = df_transacoes.groupby('ID_PGTO').agg(
        total_pago=('VL', 'sum'),
        num_pagamentos=('VL', 'count'),
        ultimo_pagamento=('DT_REFE', 'max')
    )

    rcbe_agg = df_transacoes.groupby('ID_RCBE').agg(
        total_recebido=('VL', 'sum'),
        num_recebimentos=('VL', 'count'),
        ultimo_recebimento=('DT_REFE', 'max')
    )

    features_df = features_df.join(pgto_agg, how='left')
    features_df = features_df.join(rcbe_agg, how='left')

    # Feature: Recency of last activity
    features_df['ultima_atividade'] = features_df[['ultimo_pagamento', 'ultimo_recebimento']].max(axis=1)
    features_df['dias_desde_ultima_atividade'] = (snapshot_date - features_df['ultima_atividade']).dt.days

    final_features = features_df[[
        'VL_FATU', 'VL_SLDO', 'idade_conta_dias', 'DS_CNAE',
        'total_pago', 'num_pagamentos', 'total_recebido', 'num_recebimentos',
        'dias_desde_ultima_atividade'
    ]].copy()

    final_features.fillna(0, inplace=True)

    print("Feature engineering complete.")
    return final_features

def map_clusters_to_maturity(model_results: pd.DataFrame) -> pd.DataFrame:
    """
    Maps K-Means cluster labels to meaningful maturity names based on cluster centroids.
    """
    print("\nMapping cluster labels to maturity names...")
    # Analyze the characteristics of each cluster by looking at the mean of its features
    cluster_centroids = model_results.groupby('cluster').mean(numeric_only=True)
    
    # Sort clusters by a key maturity indicator (e.g., total revenue) to help assign labels
    # in a logical order from 'Iniciante' to 'Madura'.
    sorted_clusters = cluster_centroids.sort_values(by='total_recebido', ascending=True).index

    # Create a more robust mapping logic. A simple sort might not be enough.
    # 'Declínio' is often characterized by high recency (long time since last activity)
    # and lower transactional values compared to its peak.
    decline_cluster = cluster_centroids['dias_desde_ultima_atividade'].idxmax()
    
    # The other stages can be sorted by total revenue/invoicing.
    remaining_clusters = [c for c in sorted_clusters if c != decline_cluster]
    
    # Create the mapping dictionary
    cluster_map = {decline_cluster: 'Declínio'}
    
    # Assign the other stages based on sorted revenue
    other_stages = ['Iniciante', 'Expansão', 'Madura']
    for i, cluster_id in enumerate(sorted(remaining_clusters, key=lambda c: cluster_centroids.loc[c, 'total_recebido'])):
        # Ensure we don't run out of stages if k is different than 4
        if i < len(other_stages):
            cluster_map[cluster_id] = other_stages[i]

    print("Cluster to Maturity Name Mapping:", cluster_map)
    
    # Apply the mapping to the results DataFrame
    model_results['nova_MATU'] = model_results['cluster'].map(cluster_map)
    return model_results

def update_maturity_in_db(results_df: pd.DataFrame, db_path: str):
    """
    Updates the MATURIDADE table in the database with the new classifications.
    """
    print("\nPreparing to update the database...")
    update_data = results_df[['nova_MATU']].reset_index()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "UPDATE MATURIDADE SET MATU = ? WHERE ID = ?",
                [(row['nova_MATU'], row['ID']) for index, row in update_data.iterrows()]
            )
            conn.commit()
            print(f"Successfully updated {cursor.rowcount} rows in the MATURIDADE table.")
    except sqlite3.Error as e:
        print(f"Database update failed: {e}")

def run_classification_and_update():
    """
    Main function to run the full pipeline: load, process, classify, and update.
    """
    df_id, df_transacoes, df_maturidade = load_data(DB_PATH)
    if df_id.empty:
        print("Could not run classification due to data loading errors.")
        return

    # Determine the number of clusters (k) from existing maturity stages
    k = df_maturidade['MATU'].nunique()
    print(f"Found {k} unique maturity stages. Setting k={k} for K-Means.")

    df_features = create_features(df_id, df_transacoes)

    # Define numeric and categorical features for the preprocessing pipeline
    numeric_features = df_features.select_dtypes(include=['number']).columns.tolist()
    categorical_features = ['DS_CNAE']

    # Preprocessor to scale numeric data and one-hot encode categorical data
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ],
        remainder='passthrough'
    )

    # Full pipeline with preprocessing and K-Means clustering
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('kmeans', KMeans(n_clusters=k, random_state=42, n_init='auto'))
    ])

    print("Training K-Means model with preprocessing pipeline...")
    # Fit the model and get cluster assignments
    df_features['cluster'] = pipeline.fit_predict(df_features)

    # Map cluster IDs to meaningful maturity stage names
    results_df = map_clusters_to_maturity(df_features)
    
    print("\n--- Classification Results Sample ---")
    # Join original maturity for comparison
    final_results = results_df.join(df_maturidade.set_index('ID')['MATU'].rename('antiga_MATU'))
    print(final_results[['antiga_MATU', 'nova_MATU', 'total_recebido', 'dias_desde_ultima_atividade']].head())

    # Update the database with the new classifications
    update_maturity_in_db(results_df, DB_PATH)

if __name__ == '__main__':
    run_classification_and_update()
