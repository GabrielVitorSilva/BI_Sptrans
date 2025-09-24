# data_loader.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from connection import get_postgres_connection

def get_full_date_range():
    """Retorna um range de datas fixo para a geração de todos os mocks."""
    return pd.date_range(datetime(2025, 1, 1), datetime(2025, 8, 31))

# --- FUNÇÕES MODIFICADAS PARA ACEITAR FILTRO DE DATA ---

@st.cache_data
def load_all_transactions(start_date, end_date):
    date_rng = get_full_date_range()
    n_records = len(date_rng) * 10
    data = {
        'unique_id': [f"trans_{i}" for i in range(n_records)],
        'transaction_date': np.random.choice(date_rng, n_records),
        'payment_method': np.random.choice(['PIX', 'DEBIT', 'MONEY', 'CREDIT', 'LIST'], n_records, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
        'paid_value': np.random.uniform(10, 150, n_records),
        'pdv_id': np.random.randint(1, 21, n_records),
        'accredited_id': np.random.randint(1, 6, n_records)
    }
    df = pd.DataFrame(data)
    df['paid_value'] = df['paid_value'].astype(float).round(2)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    
    # Adicionado: Filtra o DataFrame gerado com base nas datas
    mask = (df['transaction_date'].dt.date >= start_date) & (df['transaction_date'].dt.date <= end_date)
    return df.loc[mask].copy()

@st.cache_data
def load_device_revenue_log(start_date, end_date):
    date_rng = get_full_date_range()
    n_records = 500
    data = {
        'transaction_date': np.random.choice(date_rng, n_records),
        'device_type': np.random.choice(['POS', 'Totem', 'App', 'WhatsApp'], n_records, p=[0.6, 0.15, 0.1, 0.15]),
        'value': np.random.uniform(15, 120, n_records),
        'pdv_id': np.random.randint(1, 21, n_records),
        'serial': [f"SERIAL_{np.random.randint(100, 200)}" for _ in range(n_records)]
    }
    df = pd.DataFrame(data)
    df['value'] = df['value'].astype(float).round(2)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # Adicionado: Filtra o DataFrame gerado com base nas datas
    mask = (df['transaction_date'].dt.date >= start_date) & (df['transaction_date'].dt.date <= end_date)
    return df.loc[mask].copy()

@st.cache_data
def load_daily_sales_report(start_date, end_date):
    date_rng = get_full_date_range()
    data = {
        'data': date_rng,
        'pdv': [f"PDV {np.random.randint(1, 21)}" for _ in date_rng],
        'credenciado': [f"Credenciado {np.random.randint(1, 6)}" for _ in date_rng],
        'vc': np.random.uniform(1000, 5000, len(date_rng)),
        've': np.random.uniform(1000, 5000, len(date_rng)),
        'vt': np.random.uniform(1000, 5000, len(date_rng)),
        'celular': np.random.uniform(500, 2000, len(date_rng)),
        'credito': np.random.uniform(200, 1000, len(date_rng)),
        'lista': np.random.uniform(3000, 8000, len(date_rng)),
    }
    df = pd.DataFrame(data)
    df['total'] = df[['vc', 've', 'vt', 'celular', 'credito', 'lista']].sum(axis=1)
    df['data'] = pd.to_datetime(df['data'])
    
    # Adicionado: Filtra o DataFrame gerado com base nas datas
    mask = (df['data'].dt.date >= start_date) & (df['data'].dt.date <= end_date)
    return df.loc[mask].copy()

# --- FUNÇÕES QUE NÃO FORAM MODIFICADAS ---

@st.cache_data
def load_cash_movimentation():
    data = {'status': ['Received', 'Pending', 'Overdue'], 'value': [2000000, 500000, 150000]}
    return pd.DataFrame(data)

@st.cache_data
def load_payout_summary():
    data = {'category': ['Convenience Fee', 'Accredited Commission', 'Creditor Commission', 'Network Commission', 'SPTrans Payout', 'Taxes'], 'value': [120000, 350000, 450000, 200000, 1500000, 80000]}
    return pd.DataFrame(data)

# --- SUA FUNÇÃO COM SQL - INTACTA ---
@st.cache_data(ttl=300)
def load_entity_counts():
    query = (
        "SELECT total_pdv_units, pos_terminal_count, list_pos_terminal_count, totem_terminal_count "
        "FROM entity_counts LIMIT 1;"
    )
    try:
        conn = get_postgres_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("View mv_entity_counts não retornou linhas.")
                total_pdv_units, pos_terminal_count, list_pos_terminal_count, totem_terminal_count = row
                return {
                    'total_pdv_units': int(total_pdv_units) if total_pdv_units is not None else 0,
                    'pos_terminal_count': int(pos_terminal_count) if pos_terminal_count is not None else 0,
                    'totem_terminal_count': int(totem_terminal_count) if totem_terminal_count is not None else 0,
                    'list_pos_terminal_count': int(list_pos_terminal_count) if list_pos_terminal_count is not None else 0,
                }
    except Exception as exc:
        raise RuntimeError(f"Falha ao consultar Postgres (EntityCounts): {exc}")