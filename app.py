# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import io
from data_loader import (
    load_all_transactions,
    load_cash_movimentation,
    load_device_revenue_log,
    load_daily_sales_report,
    load_entity_counts
)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="BI Rede Recarga",
    page_icon="📊",
    layout="wide"
)

# --- CONSTANTES ---
REFRESH_INTERVAL_SECONDS = 15

# --- CARREGAMENTO DOS DADOS ---
df_trans = load_all_transactions()
df_cash = load_cash_movimentation()
df_device = load_device_revenue_log()
df_daily = load_daily_sales_report()
entity_counts = load_entity_counts()


# --- FUNÇÕES DE RELATÓRIOS INDIVIDUAIS (sem alterações) ---
def report_kpi_faturamento(df_trans):
    st.title("💰 Financeiro: Faturamento Geral")
    last_month_period = df_trans['transaction_date'].dt.to_period('M').max()
    df_filtered = df_trans[df_trans['transaction_date'].dt.to_period('M') == last_month_period].copy()
    faturamento_atual = df_filtered['paid_value'].sum()
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Faturamento Mensal", f"R$ {faturamento_atual:,.2f}")
    col2.metric("Ticket Médio", f"R$ {df_filtered['paid_value'].mean():,.2f}")

def report_chart_payment_methods(df_trans):
    st.title("💰 Financeiro: Receita por Método de Pagamento")
    last_month_period = df_trans['transaction_date'].dt.to_period('M').max()
    df_filtered = df_trans[df_trans['transaction_date'].dt.to_period('M') == last_month_period].copy()
    payment_revenue = df_filtered.groupby('payment_method')['paid_value'].sum().reset_index()
    fig = px.pie(payment_revenue, names='payment_method', values='paid_value', hole=0.4, title="Participação por Método de Pagamento")
    fig.update_layout(legend_orientation="h", margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

def report_chart_contas_receber(df_cash):
    st.title("💰 Financeiro: Saúde de Contas a Receber")
    fig = px.bar(df_cash, x='status', y='value', color='status', title="Status de Transações em Dinheiro", color_discrete_map={'Recebido': 'green', 'Pendente': 'orange', 'Vencido': 'red'})
    fig.update_layout(showlegend=False, margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

def report_chart_vendas_canal(df_device):
    st.title("📈 Vendas: Faturamento por Canal")
    last_month_period = df_device['transaction_date'].dt.to_period('M').max()
    df_device_filtered = df_device[df_device['transaction_date'].dt.to_period('M') == last_month_period].copy()
    channel_revenue = df_device_filtered.groupby('device_type')['value'].agg('sum').reset_index()
    fig = px.bar(channel_revenue, x='device_type', y='value', text_auto='.2s', title="Faturamento Total por Canal de Origem")
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

def report_chart_horarios_pico(df_device):
    st.title("📈 Vendas: Análise de Horários de Pico")
    last_month_period = df_device['transaction_date'].dt.to_period('M').max()
    df_device_filtered = df_device[df_device['transaction_date'].dt.to_period('M') == last_month_period].copy()
    df_device_filtered['hour'] = df_device_filtered['transaction_date'].dt.hour
    hourly_sales = df_device_filtered.groupby('hour')['value'].sum().reset_index()
    hourly_sales['hour'] = hourly_sales['hour'].astype(str)
    fig = px.bar(hourly_sales, x='hour', y='value', title="Volume de Vendas por Hora do Dia")
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

def report_kpi_terminais(entity_counts):
    st.title("🏢 Operacional: Distribuição de Terminais")
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de PDVs", entity_counts['total_pdv_units'])
    col2.metric("Terminais POS", entity_counts['pos_terminal_count'])
    col3.metric("Terminais Totem", entity_counts['totem_terminal_count'])
    col4.metric("Terminais Lista", entity_counts['list_pos_terminal_count'])

def report_table_rankings(df_daily):
    st.title("🏢 Operacional: Rankings de Desempenho (Top 5)")
    last_month_period = df_daily['data'].dt.to_period('M').max()
    df_daily_filtered = df_daily[df_daily['data'].dt.to_period('M') == last_month_period].copy()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("PDVs por Faturamento")
        pdv_ranking = df_daily_filtered.groupby('pdv')['total'].sum().nlargest(5).reset_index()
        st.dataframe(pdv_ranking, hide_index=True, use_container_width=True)
    with col2:
        st.subheader("Credenciados por Faturamento")
        credenciado_ranking = df_daily_filtered.groupby('credenciado')['total'].sum().nlargest(5).reset_index()
        st.dataframe(credenciado_ranking, hide_index=True, use_container_width=True)

REPORTS = [
    {"name": "Financeiro: Faturamento Geral", "func": report_kpi_faturamento, "args": [df_trans]},
    {"name": "Financeiro: Métodos de Pagamento", "func": report_chart_payment_methods, "args": [df_trans]},
    {"name": "Financeiro: Contas a Receber", "func": report_chart_contas_receber, "args": [df_cash]},
    {"name": "Vendas: Faturamento por Canal", "func": report_chart_vendas_canal, "args": [df_device]},
    {"name": "Vendas: Horários de Pico", "func": report_chart_horarios_pico, "args": [df_device]},
    {"name": "Operacional: Distribuição de Terminais", "func": report_kpi_terminais, "args": [entity_counts]},
    {"name": "Operacional: Rankings de Desempenho", "func": report_table_rankings, "args": [df_daily]},
]
REPORT_NAMES = [report["name"] for report in REPORTS]

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'current_dashboard_index' not in st.session_state:
    st.session_state.current_dashboard_index = 0
if 'autorotate' not in st.session_state:
    st.session_state.autorotate = True

# --- BARRA LATERAL COM CONTROLES ---
st.sidebar.title("Painel de Controle")
st.sidebar.markdown("Use os controles abaixo para navegar.")
st.sidebar.toggle("Rotação Automática", key='autorotate')
st.sidebar.divider()
st.sidebar.subheader("Navegação Manual")

def handle_next():
    st.session_state.current_dashboard_index = (st.session_state.current_dashboard_index + 1) % len(REPORTS)
    st.session_state.autorotate = False

def handle_previous():
    st.session_state.current_dashboard_index = (st.session_state.current_dashboard_index - 1 + len(REPORTS)) % len(REPORTS)
    st.session_state.autorotate = False

def handle_select():
    # A callback agora lê o valor do widget e atualiza o índice
    st.session_state.current_dashboard_index = REPORT_NAMES.index(st.session_state.selected_dashboard_key)
    st.session_state.autorotate = False

st.sidebar.selectbox(
    "Ir para Relatório:",
    options=REPORT_NAMES,
    index=st.session_state.current_dashboard_index,
    key='selected_dashboard_key', # Usamos uma chave para o widget
    on_change=handle_select
)

col1, col2 = st.sidebar.columns(2)
col1.button("◀️ Anterior", on_click=handle_previous, use_container_width=True)
col2.button("Próximo ▶️", on_click=handle_next, use_container_width=True)

# --- LÓGICA PRINCIPAL ---
current_index = st.session_state.current_dashboard_index
report_to_display = REPORTS[current_index]
report_to_display["func"](*report_to_display["args"])

if st.session_state.autorotate:
    # A rotação automática agora APENAS atualiza o índice.
    st.session_state.current_dashboard_index = (current_index + 1) % len(REPORTS)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    for i in range(REFRESH_INTERVAL_SECONDS):
        progress_bar.progress((i + 1) / REFRESH_INTERVAL_SECONDS)
        status_text.caption(f"Próximo relatório em {REFRESH_INTERVAL_SECONDS - i} segundos...")
        time.sleep(1)
    status_text.empty()
    progress_bar.empty()
    st.rerun()