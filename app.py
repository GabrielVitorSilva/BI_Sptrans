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

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'current_dashboard_index' not in st.session_state:
    st.session_state.current_dashboard_index = 0
if 'autorotate' not in st.session_state:
    st.session_state.autorotate = True


# --- FUNÇÃO PARA GERAR O PDF (VERSÃO COMPLETA E CORRIGIDA) ---
def generate_pdf_report(df_trans, df_cash, df_device, df_daily, entity_counts):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "Relatório Consolidado - Rede Recarga", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Gerado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    def add_chart_to_pdf(fig, title):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        img_bytes = fig.to_image(format="png", width=800, height=450, scale=2)
        pdf.image(io.BytesIO(img_bytes), x=10, y=25, w=190)
    
    # --- Relatórios Financeiros ---
    last_month_period = df_trans['transaction_date'].dt.to_period('M').max()
    df_filtered_trans = df_trans[df_trans['transaction_date'].dt.to_period('M') == last_month_period].copy()
    
    # 1. KPIs de Faturamento
    faturamento_atual = df_filtered_trans['paid_value'].sum()
    ticket_medio = df_filtered_trans['paid_value'].mean()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Financeiro: Faturamento Geral", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Faturamento Mensal: R$ {faturamento_atual:,.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Ticket Médio: R$ {ticket_medio:,.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 2. Gráfico: Métodos de Pagamento
    payment_revenue = df_filtered_trans.groupby('payment_method')['paid_value'].sum().reset_index()
    fig_payment = px.pie(payment_revenue, names='payment_method', values='paid_value', hole=0.4, template="plotly_white")
    add_chart_to_pdf(fig_payment, "Financeiro: Receita por Método de Pagamento")

    # 3. Gráfico: Contas a Receber
    fig_cash = px.bar(df_cash, x='status', y='value', color='status',
                      color_discrete_map={'Recebido': 'green', 'Pendente': 'orange', 'Vencido': 'red'}, template="plotly_white")
    add_chart_to_pdf(fig_cash, "Financeiro: Saúde de Contas a Receber")

    # --- Relatórios de Vendas ---
    last_month_period_device = df_device['transaction_date'].dt.to_period('M').max()
    df_filtered_device = df_device[df_device['transaction_date'].dt.to_period('M') == last_month_period_device].copy()

    # 4. Gráfico: Vendas por Canal
    channel_revenue = df_filtered_device.groupby('device_type')['value'].agg('sum').reset_index()
    fig_channel = px.bar(channel_revenue, x='device_type', y='value', text_auto='.2s', template="plotly_white")
    add_chart_to_pdf(fig_channel, "Vendas: Faturamento por Canal")
    
    # 5. Gráfico: Horários de Pico
    df_filtered_device['hour'] = df_filtered_device['transaction_date'].dt.hour
    hourly_sales = df_filtered_device.groupby('hour')['value'].sum().reset_index()
    hourly_sales['hour'] = hourly_sales['hour'].astype(str)
    fig_hourly = px.bar(hourly_sales, x='hour', y='value', template="plotly_white")
    add_chart_to_pdf(fig_hourly, "Vendas: Análise de Horários de Pico")
    
    # --- Relatórios Operacionais ---
    # 6. KPIs de Terminais
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Operacional: Distribuição de Terminais", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Total de PDVs: {entity_counts['total_pdv_units']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Terminais POS: {entity_counts['pos_terminal_count']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Terminais Totem: {entity_counts['totem_terminal_count']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Terminais Lista: {entity_counts['list_pos_terminal_count']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # 7. Tabelas de Ranking
    last_month_period_daily = df_daily['data'].dt.to_period('M').max()
    df_daily_filtered = df_daily[df_daily['data'].dt.to_period('M') == last_month_period_daily].copy()
    pdv_ranking = df_daily_filtered.groupby('pdv')['total'].sum().nlargest(5).reset_index()
    credenciado_ranking = df_daily_filtered.groupby('credenciado')['total'].sum().nlargest(5).reset_index()
    
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Operacional: Rankings de Desempenho (Top 5)", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.ln(5)
    
    # Tabela de PDVs
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "PDVs por Faturamento", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    for index, row in pdv_ranking.iterrows():
        pdf.cell(80, 8, str(row['pdv']), border=1)
        pdf.cell(40, 8, f"R$ {row['total']:,.2f}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    
    # Tabela de Credenciados
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Credenciados por Faturamento", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    for index, row in credenciado_ranking.iterrows():
        pdf.cell(80, 8, str(row['credenciado']), border=1)
        pdf.cell(40, 8, f"R$ {row['total']:,.2f}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())

# --- O RESTO DO CÓDIGO PERMANECE IGUAL ---
# (As funções report_*, listas de relatórios e a lógica da sidebar não precisam de alteração)
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
        st.dataframe(pdv_ranking, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Credenciados por Faturamento")
        credenciado_ranking = df_daily_filtered.groupby('credenciado')['total'].sum().nlargest(5).reset_index()
        st.dataframe(credenciado_ranking, use_container_width=True, hide_index=True)

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
st.sidebar.title("Painel de Controle")
st.sidebar.markdown("Use os controles abaixo para navegar.")
st.sidebar.toggle("Rotação Automática", value=True, key='autorotate')
st.sidebar.divider()
st.sidebar.subheader("Exportar Relatório")
if st.sidebar.button("Baixar Relatório em PDF", use_container_width=True):
    with st.spinner("Gerando PDF, por favor aguarde..."):
        pdf_data = generate_pdf_report(df_trans, df_cash, df_device, df_daily, entity_counts)
        st.sidebar.download_button(
            label="Clique para baixar o PDF",
            data=pdf_data,
            file_name=f"relatorio_rede_recarga_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
st.sidebar.divider()
st.sidebar.subheader("Navegação Manual")
def handle_next():
    st.session_state.current_dashboard_index = (st.session_state.current_dashboard_index + 1) % len(REPORTS)
    st.session_state.autorotate = False
def handle_previous():
    st.session_state.current_dashboard_index = (st.session_state.current_dashboard_index - 1 + len(REPORTS)) % len(REPORTS)
    st.session_state.autorotate = False
def handle_select():
    st.session_state.current_dashboard_index = REPORT_NAMES.index(st.session_state.selected_dashboard)
    st.session_state.autorotate = False
st.sidebar.selectbox("Ir para Relatório:", options=REPORT_NAMES, index=st.session_state.current_dashboard_index, key='selected_dashboard', on_change=handle_select)
col1, col2 = st.sidebar.columns(2)
col1.button("◀️ Anterior", use_container_width=True, on_click=handle_previous)
col2.button("Próximo ▶️", use_container_width=True, on_click=handle_next)
current_index = st.session_state.current_dashboard_index
report_to_display = REPORTS[current_index]
report_to_display["func"](*report_to_display["args"])
if st.session_state.autorotate:
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