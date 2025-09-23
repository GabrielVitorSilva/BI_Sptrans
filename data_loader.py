# data_loader.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
"""
ATENÇÃO: Este arquivo contém dados de exemplo (mocks).
Substitua as funções aqui presentes pela sua lógica real de conexão 
e extração de dados do banco de dados PostgreSQL.
"""

def get_date_range():
    """Retorna um range de datas para os mocks."""
    end_date = datetime(2025, 8, 31)
    start_date = datetime(2025, 1, 1)
    return pd.date_range(start_date, end_date)

@st.cache_data
def load_all_transactions():
    """Carrega dados transacionais. Substitua pelo acesso a `mv_all_transactions`."""
    date_rng = get_date_range()
    n_records = len(date_rng) * 10 # 10 transações por dia
    
    data = {
        'unique_id': [f"trans_{i}" for i in range(n_records)],
        'transaction_date': np.random.choice(date_rng, n_records),
        'payment_method': np.random.choice(
            ['PIX', 'DEBIT', 'MONEY', 'CREDIT', 'LIST'], 
            n_records, 
            p=[0.3, 0.25, 0.2, 0.15, 0.1]
        ),
        'paid_value': np.random.uniform(10, 150, n_records),
        'pdv_id': np.random.randint(1, 21, n_records),
        'accredited_id': np.random.randint(1, 6, n_records)
    }
    df = pd.DataFrame(data)
    df['paid_value'] = df['paid_value'].astype(float).round(2)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df

@st.cache_data
def load_cash_movimentation():
    """Carrega dados de movimentação de caixa. Substitua pelo acesso a `mv_recharge_status`."""
    data = {
        'status': ['Received', 'Pending', 'Overdue'],
        'value': [2000000, 500000, 150000]
    }
    return pd.DataFrame(data)

@st.cache_data
def load_payout_summary():
    """Carrega dados de comissões. Substitua pelo acesso a `mv_card_payout_summary` e `mv_phone_payout_summary`."""
    data = {
        'category': ['Convenience Fee', 'Accredited Commission', 'Creditor Commission', 'Network Commission', 'SPTrans Payout', 'Taxes'],
        'value': [120000, 350000, 450000, 200000, 1500000, 80000]
    }
    return pd.DataFrame(data)
    
@st.cache_data
def load_device_revenue_log():
    """Carrega dados de receita por dispositivo. Substitua pelo acesso a `mv_device_revenue_log`."""
    date_rng = get_date_range()
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
    return df

@st.cache_data
def load_daily_sales_report():
    """Carrega relatório diário. Substitua pelo acesso a `mv_daily_sales_report`."""
    date_rng = get_date_range()
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
    return df

@st.cache_data
def load_entity_counts():
    """Carrega contagem de entidades. Substitua pelo acesso a `mv_entity_counts`."""
    return {
        'total_pdv_units': 540,
        'pos_terminal_count': 480,
        'totem_terminal_count': 50,
        'list_pos_terminal_count': 10
    }