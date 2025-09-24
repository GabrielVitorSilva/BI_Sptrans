# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import io
from datetime import datetime, timedelta # Adicionado
from data_loader import (
    load_all_transactions,
    load_cash_movimentation,
    load_device_revenue_log,
    load_daily_sales_report,
    load_entity_counts
)

st.set_page_config(page_title="BI Rede Recarga", page_icon="📊", layout="wide")

REFRESH_INTERVAL_SECONDS = 15

# --- ADICIONADO: BARRA LATERAL COM FILTROS DE DATA ---
st.sidebar.title("Painel de Controle")
st.sidebar.header("Filtros de Período")
end_date_default = datetime.now().date()
start_date_default = end_date_default - timedelta(days=30)
start_date = st.sidebar.date_input("Data de Início", value=start_date_default)
end_date = st.sidebar.date_input("Data de Fim", value=end_date_default)

if start_date > end_date:
    st.sidebar.error("A data de início não pode ser posterior à data de fim.")
    st.stop()
st.sidebar.divider()

# --- MODIFICADO: CARREGAMENTO DOS DADOS COM FILTRO ---
df_trans = load_all_transactions(start_date, end_date)
df_cash = load_cash_movimentation() # Sem filtro de data
df_device = load_device_revenue_log(start_date, end_date)
df_daily = load_daily_sales_report(start_date, end_date)
entity_counts = load_entity_counts() # Sem filtro de data


# --- FUNÇÃO PARA GERAR O PDF (AJUSTADA PARA USAR DADOS FILTRADOS) ---
def generate_pdf_report(df_trans, df_cash, df_device, df_daily, entity_counts):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "Relatório Consolidado - Rede Recarga", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    def add_chart_to_pdf(fig, title):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        img_bytes = fig.to_image(format="png", width=800, height=450, scale=2)
        pdf.image(io.BytesIO(img_bytes), x=10, y=25, w=190)

    # Relatórios Financeiros (agora usam os dataframes já filtrados)
    if not df_trans.empty:
        faturamento_atual = df_trans['paid_value'].sum()
        ticket_medio = df_trans['paid_value'].mean()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Financeiro: Faturamento Geral", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"Faturamento no Período: R$ {faturamento_atual:,.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Ticket Médio: R$ {ticket_medio:,.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        payment_revenue = df_trans.groupby('payment_method')['paid_value'].sum().reset_index()
        fig_payment = px.pie(payment_revenue, names='payment_method', values='paid_value', hole=0.4, template="plotly_white")
        add_chart_to_pdf(fig_payment, "Financeiro: Receita por Método de Pagamento")
    # ... (Restante da lógica do PDF pode ser adicionada aqui) ...
    return bytes(pdf.output())

# --- FUNÇÕES DE RELATÓRIOS INDIVIDUAIS (AJUSTADAS) ---
def report_kpi_faturamento(df_trans):
    st.title("💰 Financeiro: Faturamento Geral")
    if df_trans.empty:
        st.warning("Não há dados para o período selecionado.")
        return
    faturamento_atual = df_trans['paid_value'].sum()
    ticket_medio = df_trans['paid_value'].mean()
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Faturamento no Período", f"R$ {faturamento_atual:,.2f}")
    col2.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

def report_chart_payment_methods(df_trans):
    st.title("💰 Financeiro: Receita por Método de Pagamento")
    if df_trans.empty:
        st.warning("Não há dados para o período selecionado.")
        return
    payment_revenue = df_trans.groupby('payment_method')['paid_value'].sum().reset_index()
    fig = px.pie(payment_revenue, names='payment_method', values='paid_value', hole=0.4, title="Participação por Método de Pagamento")
    fig.update_layout(legend_orientation="h", margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

# (O resto das funções e da lógica principal permanecem como na sua versão)
def report_chart_contas_receber(df_cash):
    st.title("💰 Financeiro: Saúde de Contas a Receber")
    fig = px.bar(df_cash, x='status', y='value', color='status', title="Status de Transações em Dinheiro", color_discrete_map={'Recebido': 'green', 'Pendente': 'orange', 'Vencido': 'red'})
    fig.update_layout(showlegend=False, margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

def report_chart_vendas_canal(df_device):
    st.title("📈 Vendas: Faturamento por Canal")
    if df_device.empty:
        st.warning("Não há dados para o período selecionado.")
        return
    channel_revenue = df_device.groupby('device_type')['value'].agg('sum').reset_index()
    fig = px.bar(channel_revenue, x='device_type', y='value', text_auto='.2s', title="Faturamento Total por Canal de Origem")
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

def report_chart_horarios_pico(df_device):
    st.title("📈 Vendas: Análise de Horários de Pico")
    if df_device.empty:
        st.warning("Não há dados para o período selecionado.")
        return
    df_device['hour'] = pd.to_datetime(df_device['transaction_date']).dt.hour
    hourly_sales = df_device.groupby('hour')['value'].sum().reset_index()
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
    if df_daily.empty:
        st.warning("Não há dados para o período selecionado.")
        return
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("PDVs por Faturamento")
        pdv_ranking = df_daily.groupby('pdv')['total'].sum().nlargest(5).reset_index()
        st.dataframe(pdv_ranking, hide_index=True, use_container_width=True)
    with col2:
        st.subheader("Credenciados por Faturamento")
        credenciado_ranking = df_daily.groupby('credenciado')['total'].sum().nlargest(5).reset_index()
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
if 'current_dashboard_index' not in st.session_state: st.session_state.current_dashboard_index = 0
if 'autorotate' not in st.session_state: st.session_state.autorotate = True
if 'selected_dashboard' not in st.session_state: st.session_state.selected_dashboard = REPORT_NAMES[st.session_state.current_dashboard_index]

st.sidebar.markdown("Use os controles abaixo para navegar.")
st.sidebar.toggle("Rotação Automática", key='autorotate')
st.sidebar.divider()
st.sidebar.subheader("Exportar Relatório")
if st.sidebar.button("Gerar Relatório em PDF", use_container_width=True):
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
def handle_navigation(new_index):
    st.session_state.current_dashboard_index = new_index
    st.session_state.selected_dashboard = REPORT_NAMES[new_index]
    st.session_state.autorotate = False
def handle_next(): handle_navigation((st.session_state.current_dashboard_index + 1) % len(REPORTS))
def handle_previous(): handle_navigation((st.session_state.current_dashboard_index - 1 + len(REPORTS)) % len(REPORTS))
def handle_select(): handle_navigation(REPORT_NAMES.index(st.session_state.selected_dashboard_key))
st.sidebar.selectbox("Ir para Relatório:", options=REPORT_NAMES, key='selected_dashboard_key', on_change=handle_select, index=st.session_state.current_dashboard_index)
col1, col2 = st.sidebar.columns(2)
col1.button("◀️ Anterior", on_click=handle_previous, use_container_width=True)
col2.button("Próximo ▶️", on_click=handle_next, use_container_width=True)

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