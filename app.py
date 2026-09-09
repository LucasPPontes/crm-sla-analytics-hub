import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import faicons as fa

from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_plotly

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.crm_service import load_crm_data
from backend.services.sla_service import (
    load_raw_data,
    get_options,
    filter_chamados,
    get_executiva_metrics,
    get_sla_metrics,
    get_contratos_metrics,
    get_equipe_metrics,
    get_chamados_table
)

# -----------------------------------------------------------------------------
# PLOTLY TRANSPARENT THEME HELPER WITH AUTOMARGIN (NO LABELS CUT OFF)
# -----------------------------------------------------------------------------
def apply_plotly_theme(fig, is_horizontal=False):
    left_margin = 190 if is_horizontal else 65
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
        margin=dict(l=left_margin, r=35, t=35, b=45),
        autosize=True,
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig

# Load initial SLA options
sla_opts = get_options()
clientes_list = sla_opts.get("clientes", [])
prioridades_list = sla_opts.get("prioridades", ["Crítica", "Alta", "Média", "Baixa"])
categorias_list = sla_opts.get("categorias", [])
consultores_list = sla_opts.get("consultores", [])
min_date = sla_opts.get("min_date", "2024-01-01")
max_date = sla_opts.get("max_date", "2024-12-31")

# Load CRM initial data to get account managers
crm_raw = load_crm_data()
account_managers = sorted(list(set(c["accountManager"] for c in crm_raw.get("customers", []))))
account_managers_choices = ["Todos"] + account_managers

# -----------------------------------------------------------------------------
# SHINY UI DEFINITION WITH AUTOMARGIN & INSTANT THEME SWITCHING
# -----------------------------------------------------------------------------
app_ui = ui.page_navbar(
    # 1. HUB EXECUTIVO
    ui.nav_panel(
        "Hub Executivo",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Filtros Globais", class_="fw-bold mb-3"),
                ui.input_date_range("hub_date_range", "Período:", start=min_date, end=max_date, format="yyyy-mm-dd", language="pt-BR"),
                ui.input_select("hub_am", "Gerente de Conta (CRM):", choices=account_managers_choices, selected="Todos"),
                ui.input_select("hub_status_sla", "Status SLA:", choices=["Todos", "Dentro do SLA", "Fora do SLA"], selected="Todos"),
                open="desktop"
            ),
            ui.layout_columns(
                ui.value_box("MRR Total (CRM)", ui.output_text("hub_kpi_mrr"), showcase=fa.icon_svg("dollar-sign"), theme="primary"),
                ui.value_box("Clientes Ativos", ui.output_text("hub_kpi_clients"), showcase=fa.icon_svg("users"), theme="info"),
                ui.value_box("Conformidade SLA", ui.output_text("hub_kpi_sla_pct"), showcase=fa.icon_svg("shield-halved"), theme="success"),
                ui.value_box("Pipeline de Vendas", ui.output_text("hub_kpi_pipeline"), showcase=fa.icon_svg("filter"), theme="warning"),
                ui.value_box("MTTR Médio", ui.output_text("hub_kpi_mttr"), showcase=fa.icon_svg("clock"), theme="danger"),
                ui.value_box("Receita Excedente SLA", ui.output_text("hub_kpi_extra_revenue"), showcase=fa.icon_svg("file-invoice-dollar"), theme="secondary"),
                col_widths=(4, 4, 4, 4, 4, 4)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Distribuição de Receita por Indústria (CRM)", class_="fw-bold"),
                    output_widget("hub_chart_mrr_industry")
                ),
                ui.card(
                    ui.card_header("Evolução Mensal do SLA de Solução (%)", class_="fw-bold"),
                    output_widget("hub_chart_sla_monthly")
                ),
                col_widths=(6, 6)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Estágios do Funil de Vendas", class_="fw-bold"),
                    output_widget("hub_chart_pipeline_funnel")
                ),
                ui.card(
                    ui.card_header("Consumo de Horas por Cliente (Top Excedentes)", class_="fw-bold"),
                    output_widget("hub_chart_horas_cliente")
                ),
                col_widths=(6, 6)
            )
        )
    ),

    # 2. CRM - VISÃO GERAL
    ui.nav_panel(
        "CRM - Visão Geral",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Filtros CRM", class_="fw-bold mb-3"),
                ui.input_select("crm_am_filter", "Gerente de Conta:", choices=account_managers_choices, selected="Todos"),
                ui.input_select("crm_industry_filter", "Indústria:", choices=["Todas", "Tecnologia", "Finanças", "Saúde", "Varejo", "Manufatura"], selected="Todas"),
                ui.input_select("crm_segment_filter", "Segmento:", choices=["Todos", "Enterprise", "Mid-Market", "SMB"], selected="Todos"),
                open="desktop"
            ),
            ui.layout_columns(
                ui.value_box("MRR Total", ui.output_text("crm_ov_mrr"), showcase=fa.icon_svg("dollar-sign"), theme="primary"),
                ui.value_box("ARR Estimado", ui.output_text("crm_ov_arr"), showcase=fa.icon_svg("chart-line"), theme="success"),
                ui.value_box("Ticket Médio (ACV)", ui.output_text("crm_ov_acv"), showcase=fa.icon_svg("credit-card"), theme="info"),
                ui.value_box("Total de Clientes", ui.output_text("crm_ov_total_clients"), showcase=fa.icon_svg("building"), theme="warning"),
                col_widths=(3, 3, 3, 3)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("MRR por Segmento de Mercado", class_="fw-bold"),
                    output_widget("crm_chart_mrr_segment")
                ),
                ui.card(
                    ui.card_header("MRR por Indústria", class_="fw-bold"),
                    output_widget("crm_chart_mrr_industry")
                ),
                col_widths=(6, 6)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Distribuição do Health Score dos Clientes", class_="fw-bold"),
                    output_widget("crm_chart_health_dist")
                ),
                ui.card(
                    ui.card_header("Ranking de Gerentes de Conta (MRR Gerido)", class_="fw-bold"),
                    output_widget("crm_chart_am_ranking")
                ),
                col_widths=(6, 6)
            )
        )
    ),

    # 3. CRM - FUNIL DE VENDAS
    ui.nav_panel(
        "CRM - Funil",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Filtros de Oportunidades", class_="fw-bold mb-3"),
                ui.input_select("pipeline_am_filter", "Gerente de Conta:", choices=account_managers_choices, selected="Todos"),
                ui.input_select("pipeline_stage_filter", "Estágio:", choices=["Todos", "Prospecção", "Qualificação", "Proposta", "Negociação", "Fechado-Ganha", "Fechado-Perdido"], selected="Todos"),
                open="desktop"
            ),
            ui.layout_columns(
                ui.value_box("Valor Total em Pipeline", ui.output_text("pipe_kpi_total"), showcase=fa.icon_svg("sack-dollar"), theme="primary"),
                ui.value_box("Pipeline Ponderado", ui.output_text("pipe_kpi_weighted"), showcase=fa.icon_svg("scale-balanced"), theme="info"),
                ui.value_box("Negócios Ativos", ui.output_text("pipe_kpi_active_deals"), showcase=fa.icon_svg("briefcase"), theme="warning"),
                ui.value_box("Ticket Médio do Pipeline", ui.output_text("pipe_kpi_avg_deal"), showcase=fa.icon_svg("calculator"), theme="success"),
                col_widths=(3, 3, 3, 3)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Funil de Vendas por Valor (R$)", class_="fw-bold"),
                    output_widget("pipe_chart_funnel_value")
                ),
                ui.card(
                    ui.card_header("Quantidade de Oportunidades por Estágio", class_="fw-bold"),
                    output_widget("pipe_chart_stage_count")
                ),
                col_widths=(6, 6)
            ),
            ui.card(
                ui.card_header("Lista de Oportunidades no Pipeline", class_="fw-bold"),
                ui.output_table("pipe_table_deals")
            )
        )
    ),

    # 4. CRM - SAÚDE DOS CLIENTES
    ui.nav_panel(
        "CRM - Saúde",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Filtros de Saúde", class_="fw-bold mb-3"),
                ui.input_select("health_risk_filter", "Risco de Churn:", choices=["Todos", "Alto Risco (<50)", "Atenção (50-70)", "Saudável (>70)"], selected="Todos"),
                ui.input_select("health_am_filter", "Gerente de Conta:", choices=account_managers_choices, selected="Todos"),
                open="desktop"
            ),
            ui.layout_columns(
                ui.value_box("Média Health Score", ui.output_text("health_kpi_avg_hs"), showcase=fa.icon_svg("heart-pulse"), theme="primary"),
                ui.value_box("NPS Médio", ui.output_text("health_kpi_avg_nps"), showcase=fa.icon_svg("star"), theme="success"),
                ui.value_box("Clientes em Alto Risco", ui.output_text("health_kpi_risk_count"), showcase=fa.icon_svg("triangle-exclamation"), theme="danger"),
                ui.value_box("MRR em Risco (R$)", ui.output_text("health_kpi_risk_mrr"), showcase=fa.icon_svg("circle-exclamation"), theme="warning"),
                col_widths=(3, 3, 3, 3)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Relação Health Score vs MRR", class_="fw-bold"),
                    output_widget("health_chart_scatter")
                ),
                ui.card(
                    ui.card_header("Distribuição de NPS dos Clientes", class_="fw-bold"),
                    output_widget("health_chart_nps")
                ),
                col_widths=(6, 6)
            ),
            ui.card(
                ui.card_header("Matriz de Clientes e Indicadores de Saúde", class_="fw-bold"),
                ui.output_table("health_table_customers")
            )
        )
    ),

    # 5. SLA - GESTÃO DE SLA
    ui.nav_panel(
        "SLA - Gestão",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Filtros SLA", class_="fw-bold mb-3"),
                ui.input_date_range("sla_date_range", "Período:", start=min_date, end=max_date, format="yyyy-mm-dd", language="pt-BR"),
                ui.input_selectize("sla_priorities", "Prioridades:", choices=prioridades_list, selected=prioridades_list, multiple=True),
                ui.input_select("sla_status_filter", "Status SLA:", choices=["Todos", "Dentro do SLA", "Fora do SLA"], selected="Todos"),
                open="desktop"
            ),
            ui.layout_columns(
                ui.value_box("SLA Solução (%)", ui.output_text("sla_kpi_sol_pct"), showcase=fa.icon_svg("circle-check"), theme="success"),
                ui.value_box("SLA Resposta (%)", ui.output_text("sla_kpi_resp_pct"), showcase=fa.icon_svg("reply"), theme="primary"),
                ui.value_box("MTTA (Primeira Resposta)", ui.output_text("sla_kpi_mtta"), showcase=fa.icon_svg("clock"), theme="info"),
                ui.value_box("MTTR (Tempo Solução)", ui.output_text("sla_kpi_mttr"), showcase=fa.icon_svg("hourglass-half"), theme="warning"),
                ui.value_box("Chamados Violados", ui.output_text("sla_kpi_breached_count"), showcase=fa.icon_svg("triangle-exclamation"), theme="danger"),
                col_widths=(4, 4, 4, 6, 6)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Cumprimento de SLA por Prioridade", class_="fw-bold"),
                    output_widget("sla_chart_prio_cumprimento")
                ),
                ui.card(
                    ui.card_header("Tempo Médio Real vs Alvo de SLA (Horas)", class_="fw-bold"),
                    output_widget("sla_chart_tempo_vs_alvo")
                ),
                col_widths=(6, 6)
            ),
            ui.card(
                ui.card_header("Chamados com Maior Atraso na Solução", class_="fw-bold"),
                ui.output_table("sla_table_estouro")
            )
        )
    ),

    # 6. SLA - CONTRATOS
    ui.nav_panel(
        "SLA - Contratos",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Filtros Contratos", class_="fw-bold mb-3"),
                ui.input_date_range("ctr_date_range", "Período:", start=min_date, end=max_date, format="yyyy-mm-dd", language="pt-BR"),
                ui.input_selectize("ctr_clientes", "Clientes:", choices=clientes_list, selected=[], multiple=True),
                open="desktop"
            ),
            ui.layout_columns(
                ui.value_box("Franquia Total de Horas", ui.output_text("ctr_kpi_franquia"), showcase=fa.icon_svg("business-time"), theme="primary"),
                ui.value_box("Horas Consumidas", ui.output_text("ctr_kpi_consumidas"), showcase=fa.icon_svg("clock"), theme="info"),
                ui.value_box("Taxa de Consumo Global", ui.output_text("ctr_kpi_pct_global"), showcase=fa.icon_svg("percent"), theme="warning"),
                ui.value_box("Clientes com Estouro", ui.output_text("ctr_kpi_estouros"), showcase=fa.icon_svg("user-xmark"), theme="danger"),
                ui.value_box("Faturamento Extra Estimado", ui.output_text("ctr_kpi_receita_extra"), showcase=fa.icon_svg("money-bill-wave"), theme="success"),
                col_widths=(4, 4, 4, 6, 6)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Horas Consumidas vs Contratadas por Cliente", class_="fw-bold"),
                    output_widget("ctr_chart_consumo_bar")
                ),
                ui.card(
                    ui.card_header("Histórico Mensal de Consumo e Faturamento Extra", class_="fw-bold"),
                    output_widget("ctr_chart_historico_trend")
                ),
                col_widths=(6, 6)
            ),
            ui.card(
                ui.card_header("Detalhamento do Consumo de Contratos por Cliente", class_="fw-bold"),
                ui.output_table("ctr_table_status")
            )
        )
    ),

    # 7. SLA - EQUIPE
    ui.nav_panel(
        "SLA - Equipe",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Filtros Equipe", class_="fw-bold mb-3"),
                ui.input_date_range("eq_date_range", "Período:", start=min_date, end=max_date, format="yyyy-mm-dd", language="pt-BR"),
                open="desktop"
            ),
            ui.layout_columns(
                ui.value_box("Destaque Conformidade SLA", ui.output_text("eq_kpi_top_sla"), showcase=fa.icon_svg("award"), theme="success"),
                ui.value_box("Maior Carga de Horas", ui.output_text("eq_kpi_top_horas"), showcase=fa.icon_svg("fire"), theme="warning"),
                ui.value_box("Média Horas / Consultor", ui.output_text("eq_kpi_avg_horas"), showcase=fa.icon_svg("user-clock"), theme="info"),
                ui.value_box("Média Chamados / Consultor", ui.output_text("eq_kpi_avg_chamados"), showcase=fa.icon_svg("headset"), theme="primary"),
                col_widths=(3, 3, 3, 3)
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Total de Horas Trabalhadas por Consultor", class_="fw-bold"),
                    output_widget("eq_chart_horas_consultor")
                ),
                ui.card(
                    ui.card_header("Taxa de Conformidade de SLA (%) por Consultor", class_="fw-bold"),
                    output_widget("eq_chart_sla_consultor")
                ),
                col_widths=(6, 6)
            )
        )
    ),

    # 8. SLA - TABELA DE CHAMADOS
    ui.nav_panel(
        "SLA - Chamados",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Filtros da Tabela", class_="fw-bold mb-3"),
                ui.input_text("tab_search", "Buscar chamado...", placeholder="Digite título ou ID..."),
                ui.input_selectize("tab_clientes", "Clientes:", choices=clientes_list, selected=[], multiple=True),
                ui.input_selectize("tab_categorias", "Categorias:", choices=categorias_list, selected=[], multiple=True),
                ui.input_selectize("tab_consultores", "Consultores:", choices=consultores_list, selected=[], multiple=True),
                open="desktop"
            ),
            ui.card(
                ui.card_header("Tabela Interativa de Chamados de Suporte", class_="fw-bold"),
                ui.output_table("tab_table_tickets")
            )
        )
    ),

    # KEYWORD ARGUMENTS
    title="Hub Executivo Unificado (CRM & SLA)",
    id="main_navbar",
    header=ui.tags.div(
        # CSS Styling for instant theme adaptation & margin bounds
        ui.tags.style("""
            .navbar-brand { font-weight: 700; letter-spacing: -0.5px; }
            .card { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
            .value-box { border-radius: 12px; }
            .table-responsive { max-height: 480px; overflow-y: auto; }

            /* INSTANT CLIENT-SIDE THEME ADAPTATION FOR PLOTLY CHARTS */
            html[data-bs-theme="dark"] .js-plotly-plot text { fill: #f8fafc !important; }
            html[data-bs-theme="light"] .js-plotly-plot text { fill: #0f172a !important; }
            html[data-bs-theme="dark"] .js-plotly-plot .gridlayer path { stroke: rgba(255, 255, 255, 0.12) !important; }
            html[data-bs-theme="light"] .js-plotly-plot .gridlayer path { stroke: rgba(0, 0, 0, 0.1) !important; }
            html[data-bs-theme="dark"] .js-plotly-plot .zerolinelayer path { stroke: rgba(255, 255, 255, 0.15) !important; }
            html[data-bs-theme="light"] .js-plotly-plot .zerolinelayer path { stroke: rgba(0, 0, 0, 0.12) !important; }
        """),
        # JavaScript observer for instant 0ms Plotly relayout on theme toggle + automargin
        ui.tags.script("""
            function updatePlotlyTheme() {
                const theme = document.documentElement.getAttribute('data-bs-theme') || 'dark';
                const fontColor = theme === 'dark' ? '#f8fafc' : '#0f172a';
                const template = theme === 'dark' ? 'plotly_dark' : 'plotly_white';
                
                document.querySelectorAll('.js-plotly-plot').forEach((el) => {
                    if (window.Plotly && el.layout) {
                        Plotly.relayout(el, {
                            'paper_bgcolor': 'rgba(0,0,0,0)',
                            'plot_bgcolor': 'rgba(0,0,0,0)',
                            'font.color': fontColor,
                            'template': template,
                            'xaxis.automargin': true,
                            'yaxis.automargin': true
                        });
                    }
                });
            }

            const themeObserver = new MutationObserver((mutations) => {
                mutations.forEach((m) => {
                    if (m.attributeName === 'data-bs-theme') {
                        updatePlotlyTheme();
                    }
                });
            });

            document.addEventListener('DOMContentLoaded', () => {
                themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-bs-theme'] });
                setTimeout(updatePlotlyTheme, 500);
            });
        """),
        ui.tags.div(
            {"class": "d-flex align-items-center me-3"},
            ui.input_dark_mode(id="mode", mode="dark"),
        )
    )
)

# -----------------------------------------------------------------------------
# SHINY SERVER LOGIC
# -----------------------------------------------------------------------------
def server(input, output, session):

    # Reactive Raw Data Loaders
    @reactive.calc
    def get_crm_dataset():
        return load_crm_data()

    @reactive.calc
    def get_sla_raw():
        return load_raw_data()

    # -------------------------------------------------------------------------
    # 1. HUB EXECUTIVO LOGIC
    # -------------------------------------------------------------------------
    @reactive.calc
    def hub_filtered_sla():
        df_clientes, df_chamados, _ = get_sla_raw()
        if df_chamados.empty:
            return df_chamados
        dr = input.hub_date_range()
        start_d = dr[0].strftime("%Y-%m-%d") if dr and len(dr) > 0 else None
        end_d = dr[1].strftime("%Y-%m-%d") if dr and len(dr) > 1 else None
        st_sla = input.hub_status_sla()
        return filter_chamados(df_chamados, start_date=start_d, end_date=end_d, status_sla=st_sla)

    @output
    @render.text
    def hub_kpi_mrr():
        crm = get_crm_dataset()
        custs = crm.get("customers", [])
        am = input.hub_am()
        if am != "Todos":
            custs = [c for c in custs if c.get("accountManager") == am]
        total_mrr = sum(c.get("mrr", 0) for c in custs)
        return f"R$ {total_mrr:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render.text
    def hub_kpi_clients():
        crm = get_crm_dataset()
        custs = crm.get("customers", [])
        am = input.hub_am()
        if am != "Todos":
            custs = [c for c in custs if c.get("accountManager") == am]
        return f"{len(custs)} clientes"

    @output
    @render.text
    def hub_kpi_sla_pct():
        df_f = hub_filtered_sla()
        df_cli, _, _ = get_sla_raw()
        m = get_executiva_metrics(df_f, df_cli)
        return f"{m['sla_solucao_pct']}%"

    @output
    @render.text
    def hub_kpi_pipeline():
        crm = get_crm_dataset()
        deals = crm.get("deals", [])
        am = input.hub_am()
        if am != "Todos":
            deals = [d for d in deals if d.get("accountManager") == am]
        total_pipe = sum(d.get("value", 0) for d in deals if d.get("stage") not in ["Fechado-Ganha", "Fechado-Perdido"])
        return f"R$ {total_pipe:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render.text
    def hub_kpi_mttr():
        df_f = hub_filtered_sla()
        m = get_sla_metrics(df_f)
        return f"{m['mttr_medio']} hrs"

    @output
    @render.text
    def hub_kpi_extra_revenue():
        df_f = hub_filtered_sla()
        df_cli, _, _ = get_sla_raw()
        m = get_executiva_metrics(df_f, df_cli)
        return f"R$ {m['total_faturamento_extra']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render_plotly
    def hub_chart_mrr_industry():
        crm = get_crm_dataset()
        custs = crm.get("customers", [])
        am = input.hub_am()
        if am != "Todos":
            custs = [c for c in custs if c.get("accountManager") == am]
        df = pd.DataFrame(custs)
        if df.empty or "industry" not in df.columns:
            return apply_plotly_theme(px.pie(title="Sem dados"))
        df_ind = df.groupby("industry")["mrr"].sum().reset_index()
        fig = px.pie(df_ind, values="mrr", names="industry", hole=0.4, color_discrete_sequence=px.colors.qualitative.Plotly)
        fig.update_layout(legend=dict(orientation="h", y=-0.15))
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def hub_chart_sla_monthly():
        df_f = hub_filtered_sla()
        df_cli, _, _ = get_sla_raw()
        m = get_executiva_metrics(df_f, df_cli)
        ev = m.get("evolucao_mensal", [])
        if not ev:
            return apply_plotly_theme(px.line(title="Sem dados"))
        df_ev = pd.DataFrame(ev)
        fig = px.line(df_ev, x="mes_ano", y="taxa_sla", markers=True, labels={"mes_ano": "Mês/Ano", "taxa_sla": "SLA %"})
        fig.update_traces(line_color="#3b82f6", line_width=3, marker_size=8)
        fig.update_layout(yaxis_range=[0, 105])
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def hub_chart_pipeline_funnel():
        crm = get_crm_dataset()
        deals = crm.get("deals", [])
        am = input.hub_am()
        if am != "Todos":
            deals = [d for d in deals if d.get("accountManager") == am]
        df = pd.DataFrame(deals)
        if df.empty:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        df_stage = df.groupby("stage")["value"].sum().reset_index()
        fig = px.bar(df_stage, x="stage", y="value", text_auto=".2s", color="stage", color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Valor (R$)")
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def hub_chart_horas_cliente():
        df_f = hub_filtered_sla()
        df_cli, _, _ = get_sla_raw()
        m = get_executiva_metrics(df_f, df_cli)
        cli_cons = m.get("consumo_por_cliente", [])
        if not cli_cons:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        df_c = pd.DataFrame(cli_cons).tail(8)
        fig = px.bar(df_c, y="nome_cliente", x="horas_consumidas", orientation="h", color="estouro",
                     color_discrete_map={True: "#ef4444", False: "#22c55e"},
                     labels={"nome_cliente": "Cliente", "horas_consumidas": "Horas Consumidas"})
        fig.update_layout(showlegend=True, legend_title="Estouro de Franquia")
        return apply_plotly_theme(fig, is_horizontal=True)

    # -------------------------------------------------------------------------
    # 2. CRM - VISÃO GERAL LOGIC
    # -------------------------------------------------------------------------
    @reactive.calc
    def filtered_crm_customers():
        crm = get_crm_dataset()
        custs = crm.get("customers", [])
        am = input.crm_am_filter()
        ind = input.crm_industry_filter()
        seg = input.crm_segment_filter()
        if am != "Todos":
            custs = [c for c in custs if c.get("accountManager") == am]
        if ind != "Todas":
            custs = [c for c in custs if c.get("industry") == ind]
        if seg != "Todos":
            custs = [c for c in custs if c.get("segment") == seg]
        return custs

    @output
    @render.text
    def crm_ov_mrr():
        custs = filtered_crm_customers()
        mrr = sum(c.get("mrr", 0) for c in custs)
        return f"R$ {mrr:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render.text
    def crm_ov_arr():
        custs = filtered_crm_customers()
        mrr = sum(c.get("mrr", 0) for c in custs)
        arr = mrr * 12
        return f"R$ {arr:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render.text
    def crm_ov_acv():
        custs = filtered_crm_customers()
        if not custs:
            return "R$ 0,00"
        mrr = sum(c.get("mrr", 0) for c in custs)
        acv = (mrr * 12) / len(custs)
        return f"R$ {acv:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render.text
    def crm_ov_total_clients():
        custs = filtered_crm_customers()
        return f"{len(custs)}"

    @output
    @render_plotly
    def crm_chart_mrr_segment():
        custs = filtered_crm_customers()
        df = pd.DataFrame(custs)
        if df.empty:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        df_seg = df.groupby("segment")["mrr"].sum().reset_index()
        fig = px.bar(df_seg, x="segment", y="mrr", text_auto=".2s", color="segment")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="MRR (R$)")
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def crm_chart_mrr_industry():
        custs = filtered_crm_customers()
        df = pd.DataFrame(custs)
        if df.empty:
            return apply_plotly_theme(px.pie(title="Sem dados"))
        df_ind = df.groupby("industry")["mrr"].sum().reset_index()
        fig = px.pie(df_ind, values="mrr", names="industry", hole=0.4)
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def crm_chart_health_dist():
        custs = filtered_crm_customers()
        df = pd.DataFrame(custs)
        if df.empty:
            return apply_plotly_theme(px.histogram(title="Sem dados"))
        fig = px.histogram(df, x="healthScore", nbins=10, title="", labels={"healthScore": "Health Score"})
        fig.update_traces(marker_color="#3b82f6")
        fig.update_layout(yaxis_title="Quantidade de Clientes")
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def crm_chart_am_ranking():
        custs = filtered_crm_customers()
        df = pd.DataFrame(custs)
        if df.empty:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        df_am = df.groupby("accountManager")["mrr"].sum().reset_index().sort_values(by="mrr", ascending=True)
        fig = px.bar(df_am, y="accountManager", x="mrr", orientation="h", text_auto=".2s",
                     labels={"accountManager": "Gerente de Conta", "mrr": "MRR Gerido (R$)"})
        fig.update_traces(marker_color="#10b981")
        return apply_plotly_theme(fig, is_horizontal=True)

    # -------------------------------------------------------------------------
    # 3. CRM - FUNIL DE VENDAS LOGIC
    # -------------------------------------------------------------------------
    @reactive.calc
    def filtered_crm_deals():
        crm = get_crm_dataset()
        deals = crm.get("deals", [])
        am = input.pipeline_am_filter()
        stg = input.pipeline_stage_filter()
        if am != "Todos":
            deals = [d for d in deals if d.get("accountManager") == am]
        if stg != "Todos":
            deals = [d for d in deals if d.get("stage") == stg]
        return deals

    @output
    @render.text
    def pipe_kpi_total():
        deals = filtered_crm_deals()
        total = sum(d.get("value", 0) for d in deals)
        return f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render.text
    def pipe_kpi_weighted():
        deals = filtered_crm_deals()
        weighted = sum(d.get("value", 0) * (d.get("probability", 0) / 100.0) for d in deals)
        return f"R$ {weighted:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render.text
    def pipe_kpi_active_deals():
        deals = filtered_crm_deals()
        active = [d for d in deals if d.get("stage") not in ["Fechado-Ganha", "Fechado-Perdido"]]
        return f"{len(active)}"

    @output
    @render.text
    def pipe_kpi_avg_deal():
        deals = filtered_crm_deals()
        if not deals:
            return "R$ 0,00"
        avg_val = sum(d.get("value", 0) for d in deals) / len(deals)
        return f"R$ {avg_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render_plotly
    def pipe_chart_funnel_value():
        deals = filtered_crm_deals()
        df = pd.DataFrame(deals)
        if df.empty:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        stage_order = ["Prospecção", "Qualificação", "Proposta", "Negociação", "Fechado-Ganha", "Fechado-Perdido"]
        df_stg = df.groupby("stage")["value"].sum().reindex(stage_order).fillna(0).reset_index()
        fig = px.bar(df_stg, x="stage", y="value", text_auto=".2s", color="stage")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Valor (R$)")
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def pipe_chart_stage_count():
        deals = filtered_crm_deals()
        df = pd.DataFrame(deals)
        if df.empty:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        df_cnt = df.groupby("stage")["id"].count().reset_index()
        df_cnt.columns = ["stage", "count"]
        fig = px.bar(df_cnt, x="stage", y="count", text_auto=True, color_discrete_sequence=["#8b5cf6"])
        fig.update_layout(xaxis_title="", yaxis_title="Quantidade de Negócios")
        return apply_plotly_theme(fig)

    @output
    @render.table
    def pipe_table_deals():
        deals = filtered_crm_deals()
        if not deals:
            return pd.DataFrame()
        df = pd.DataFrame(deals)[["title", "customerName", "stage", "value", "probability", "accountManager", "expectedCloseDate"]]
        df.columns = ["Oportunidade", "Cliente", "Estágio", "Valor (R$)", "Probabilidade (%)", "Gerente", "Fechamento Previsto"]
        df["Valor (R$)"] = df["Valor (R$)"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return df

    # -------------------------------------------------------------------------
    # 4. CRM - SAÚDE DOS CLIENTES LOGIC
    # -------------------------------------------------------------------------
    @reactive.calc
    def filtered_crm_health_customers():
        crm = get_crm_dataset()
        custs = crm.get("customers", [])
        risk = input.health_risk_filter()
        am = input.health_am_filter()
        if am != "Todos":
            custs = [c for c in custs if c.get("accountManager") == am]
        if risk == "Alto Risco (<50)":
            custs = [c for c in custs if c.get("healthScore", 100) < 50]
        elif risk == "Atenção (50-70)":
            custs = [c for c in custs if 50 <= c.get("healthScore", 100) <= 70]
        elif risk == "Saudável (>70)":
            custs = [c for c in custs if c.get("healthScore", 0) > 70]
        return custs

    @output
    @render.text
    def health_kpi_avg_hs():
        custs = filtered_crm_health_customers()
        if not custs: return "0"
        avg_hs = sum(c.get("healthScore", 0) for c in custs) / len(custs)
        return f"{avg_hs:.1f}"

    @output
    @render.text
    def health_kpi_avg_nps():
        custs = filtered_crm_health_customers()
        if not custs: return "0"
        avg_nps = sum(c.get("nps", 0) for c in custs) / len(custs)
        return f"{avg_nps:.1f}"

    @output
    @render.text
    def health_kpi_risk_count():
        custs = filtered_crm_health_customers()
        at_risk = [c for c in custs if c.get("healthScore", 100) < 50]
        return f"{len(at_risk)}"

    @output
    @render.text
    def health_kpi_risk_mrr():
        custs = filtered_crm_health_customers()
        risk_mrr = sum(c.get("mrr", 0) for c in custs if c.get("healthScore", 100) < 50)
        return f"R$ {risk_mrr:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render_plotly
    def health_chart_scatter():
        custs = filtered_crm_health_customers()
        df = pd.DataFrame(custs)
        if df.empty:
            return apply_plotly_theme(px.scatter(title="Sem dados"))
        fig = px.scatter(df, x="healthScore", y="mrr", size="mrr", color="segment", hover_name="name",
                         labels={"healthScore": "Health Score", "mrr": "MRR (R$)"})
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def health_chart_nps():
        custs = filtered_crm_health_customers()
        df = pd.DataFrame(custs)
        if df.empty:
            return apply_plotly_theme(px.histogram(title="Sem dados"))
        fig = px.histogram(df, x="nps", nbins=10, color_discrete_sequence=["#f59e0b"], labels={"nps": "Nota NPS"})
        fig.update_layout(yaxis_title="Clientes")
        return apply_plotly_theme(fig)

    @output
    @render.table
    def health_table_customers():
        custs = filtered_crm_health_customers()
        if not custs: return pd.DataFrame()
        df = pd.DataFrame(custs)[["name", "industry", "segment", "healthScore", "nps", "mrr", "accountManager"]]
        df.columns = ["Cliente", "Indústria", "Segmento", "Health Score", "NPS", "MRR (R$)", "Gerente"]
        df["MRR (R$)"] = df["MRR (R$)"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return df

    # -------------------------------------------------------------------------
    # 5. SLA - GESTÃO DE SLA LOGIC
    # -------------------------------------------------------------------------
    @reactive.calc
    def filtered_sla_data():
        df_cli, df_chamados, _ = get_sla_raw()
        if df_chamados.empty:
            return df_chamados
        dr = input.sla_date_range()
        start_d = dr[0].strftime("%Y-%m-%d") if dr and len(dr) > 0 else None
        end_d = dr[1].strftime("%Y-%m-%d") if dr and len(dr) > 1 else None
        prios = list(input.sla_priorities()) if input.sla_priorities() else None
        st_sla = input.sla_status_filter()
        return filter_chamados(df_chamados, start_date=start_d, end_date=end_d, prioridades=prios, status_sla=st_sla)

    @output
    @render.text
    def sla_kpi_sol_pct():
        df_f = filtered_sla_data()
        m = get_sla_metrics(df_f)
        return f"{100 - m['violados_solucao_pct']:.1f}%"

    @output
    @render.text
    def sla_kpi_resp_pct():
        df_f = filtered_sla_data()
        m = get_sla_metrics(df_f)
        return f"{100 - m['violados_resposta_pct']:.1f}%"

    @output
    @render.text
    def sla_kpi_mtta():
        df_f = filtered_sla_data()
        m = get_sla_metrics(df_f)
        return f"{m['mtta_medio']} hrs"

    @output
    @render.text
    def sla_kpi_mttr():
        df_f = filtered_sla_data()
        m = get_sla_metrics(df_f)
        return f"{m['mttr_medio']} hrs"

    @output
    @render.text
    def sla_kpi_breached_count():
        df_f = filtered_sla_data()
        m = get_sla_metrics(df_f)
        return f"{m['violados_solucao_count']}"

    @output
    @render_plotly
    def sla_chart_prio_cumprimento():
        df_f = filtered_sla_data()
        m = get_sla_metrics(df_f)
        prio_data = m.get("sla_por_prioridade", [])
        if not prio_data:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        df_prio = pd.DataFrame(prio_data)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_prio["prioridade"], y=df_prio["cumprido"], name="Cumprido", marker_color="#10b981"))
        fig.add_trace(go.Bar(x=df_prio["prioridade"], y=df_prio["violado"], name="Violado", marker_color="#ef4444"))
        fig.update_layout(barmode="stack", xaxis_title="Prioridade", yaxis_title="Chamados")
        return apply_plotly_theme(fig)

    @output
    @render_plotly
    def sla_chart_tempo_vs_alvo():
        df_f = filtered_sla_data()
        m = get_sla_metrics(df_f)
        tempo_data = m.get("tempo_medio_vs_alvo", [])
        if not tempo_data:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        df_t = pd.DataFrame(tempo_data)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_t["prioridade"], y=df_t["tempo_real"], name="Tempo Real Médio", marker_color="#3b82f6"))
        fig.add_trace(go.Bar(x=df_t["prioridade"], y=df_t["sla_alvo"], name="SLA Alvo", marker_color="#f59e0b"))
        fig.update_layout(barmode="group", xaxis_title="Prioridade", yaxis_title="Horas")
        return apply_plotly_theme(fig)

    @output
    @render.table
    def sla_table_estouro():
        df_f = filtered_sla_data()
        m = get_sla_metrics(df_f)
        est = m.get("chamados_estouro", [])
        if not est: return pd.DataFrame()
        df_est = pd.DataFrame(est)[["ticket_id", "nome_cliente", "titulo", "prioridade", "sla_solucao_alvo_hs", "tempo_solucao_hs", "atraso_hs"]]
        df_est.columns = ["ID Ticket", "Cliente", "Título", "Prioridade", "SLA Alvo (h)", "Tempo Solução (h)", "Atraso (h)"]
        return df_est

    # -------------------------------------------------------------------------
    # 6. SLA - CONTRATOS LOGIC
    # -------------------------------------------------------------------------
    @reactive.calc
    def filtered_contratos_data():
        df_cli, df_chamados, df_hist = get_sla_raw()
        if df_chamados.empty:
            return df_chamados, df_cli, df_hist
        dr = input.ctr_date_range()
        start_d = dr[0].strftime("%Y-%m-%d") if dr and len(dr) > 0 else None
        end_d = dr[1].strftime("%Y-%m-%d") if dr and len(dr) > 1 else None
        clis = list(input.ctr_clientes()) if input.ctr_clientes() else None
        df_f = filter_chamados(df_chamados, start_date=start_d, end_date=end_d, clientes=clis)
        return df_f, df_cli, df_hist

    @output
    @render.text
    def ctr_kpi_franquia():
        df_f, df_cli, df_hist = filtered_contratos_data()
        m = get_contratos_metrics(df_f, df_cli, df_hist)
        return f"{m['total_franquias']:.0f} hrs"

    @output
    @render.text
    def ctr_kpi_consumidas():
        df_f, df_cli, df_hist = filtered_contratos_data()
        m = get_contratos_metrics(df_f, df_cli, df_hist)
        return f"{m['total_consumido']:.1f} hrs"

    @output
    @render.text
    def ctr_kpi_pct_global():
        df_f, df_cli, df_hist = filtered_contratos_data()
        m = get_contratos_metrics(df_f, df_cli, df_hist)
        return f"{m['pct_consumo_global']}%"

    @output
    @render.text
    def ctr_kpi_estouros():
        df_f, df_cli, df_hist = filtered_contratos_data()
        m = get_contratos_metrics(df_f, df_cli, df_hist)
        return f"{m['clientes_estourados']}"

    @output
    @render.text
    def ctr_kpi_receita_extra():
        df_f, df_cli, df_hist = filtered_contratos_data()
        m = get_contratos_metrics(df_f, df_cli, df_hist)
        return f"R$ {m['receita_excedente']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @output
    @render_plotly
    def ctr_chart_consumo_bar():
        df_f, df_cli, df_hist = filtered_contratos_data()
        m = get_contratos_metrics(df_f, df_cli, df_hist)
        st = m.get("status_contratos", [])
        if not st:
            return apply_plotly_theme(px.bar(title="Sem dados"))
        df_st = pd.DataFrame(st)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=df_st["nome_cliente"], x=df_st["horas_consumidas"], name="Consumidas", orientation="h", marker_color="#ef4444"))
        fig.add_trace(go.Bar(y=df_st["nome_cliente"], x=df_st["horas_contratadas_mes"], name="Contratadas", orientation="h", marker_color="#10b981"))
        fig.update_layout(barmode="group", xaxis_title="Horas", yaxis_title="Cliente")
        return apply_plotly_theme(fig, is_horizontal=True)

    @output
    @render_plotly
    def ctr_chart_historico_trend():
        df_f, df_cli, df_hist = filtered_contratos_data()
        m = get_contratos_metrics(df_f, df_cli, df_hist)
        hist = m.get("historico_mensal", [])
        if not hist:
            return apply_plotly_theme(px.line(title="Sem dados"))
        df_h = pd.DataFrame(hist)
        fig = px.line(df_h, x="mes_referencia", y=["horas_consumidas", "horas_contratadas"], labels={"mes_referencia": "Mês", "value": "Horas"})
        return apply_plotly_theme(fig)

    @output
    @render.table
    def ctr_table_status():
        df_f, df_cli, df_hist = filtered_contratos_data()
        m = get_contratos_metrics(df_f, df_cli, df_hist)
        st = m.get("status_contratos", [])
        if not st: return pd.DataFrame()
        df_st = pd.DataFrame(st)[["nome_cliente", "segmento", "gerente_conta", "horas_contratadas_mes", "horas_consumidas", "pct_consumo", "horas_excedentes", "valor_faturar_extra"]]
        df_st.columns = ["Cliente", "Segmento", "Gerente", "Franquia (h)", "Consumido (h)", "Consumo (%)", "Excedente (h)", "Faturamento Extra (R$)"]
        df_st["Faturamento Extra (R$)"] = df_st["Faturamento Extra (R$)"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return df_st

    # -------------------------------------------------------------------------
    # 7. SLA - EQUIPE LOGIC
    # -------------------------------------------------------------------------
    @reactive.calc
    def filtered_equipe_data():
        df_cli, df_chamados, _ = get_sla_raw()
        if df_chamados.empty: return df_chamados
        dr = input.eq_date_range()
        start_d = dr[0].strftime("%Y-%m-%d") if dr and len(dr) > 0 else None
        end_d = dr[1].strftime("%Y-%m-%d") if dr and len(dr) > 1 else None
        return filter_chamados(df_chamados, start_date=start_d, end_date=end_d)

    @output
    @render.text
    def eq_kpi_top_sla():
        df_f = filtered_equipe_data()
        m = get_equipe_metrics(df_f)
        top = m.get("destaque_sla", {})
        return f"{top.get('consultor', 'N/A')} ({top.get('taxa_sla_pct', 0)}%)"

    @output
    @render.text
    def eq_kpi_top_horas():
        df_f = filtered_equipe_data()
        m = get_equipe_metrics(df_f)
        top = m.get("mais_horas", {})
        return f"{top.get('consultor', 'N/A')} ({top.get('horas_totais', 0)} h)"

    @output
    @render.text
    def eq_kpi_avg_horas():
        df_f = filtered_equipe_data()
        m = get_equipe_metrics(df_f)
        return f"{m.get('media_horas_consultor', 0)} hrs"

    @output
    @render.text
    def eq_kpi_avg_chamados():
        df_f = filtered_equipe_data()
        m = get_equipe_metrics(df_f)
        return f"{m.get('media_chamados_consultor', 0):.0f}"

    @output
    @render_plotly
    def eq_chart_horas_consultor():
        df_f = filtered_equipe_data()
        m = get_equipe_metrics(df_f)
        hrs = m.get("horas_por_consultor", [])
        if not hrs: return apply_plotly_theme(px.bar(title="Sem dados"))
        df_h = pd.DataFrame(hrs)
        fig = px.bar(df_h, y="consultor", x="horas_totais", orientation="h", text_auto=".1f", color_discrete_sequence=["#3b82f6"])
        fig.update_layout(xaxis_title="Horas Totais", yaxis_title="Consultor")
        return apply_plotly_theme(fig, is_horizontal=True)

    @output
    @render_plotly
    def eq_chart_sla_consultor():
        df_f = filtered_equipe_data()
        m = get_equipe_metrics(df_f)
        sla_c = m.get("sla_por_consultor", [])
        if not sla_c: return apply_plotly_theme(px.bar(title="Sem dados"))
        df_s = pd.DataFrame(sla_c)
        fig = px.bar(df_s, y="consultor", x="taxa_sla_pct", orientation="h", text_auto=".1f", color_discrete_sequence=["#10b981"])
        fig.update_layout(xaxis_title="Taxa SLA (%)", yaxis_title="Consultor", xaxis_range=[0, 105])
        return apply_plotly_theme(fig, is_horizontal=True)

    # -------------------------------------------------------------------------
    # 8. SLA - TABELA DE CHAMADOS LOGIC
    # -------------------------------------------------------------------------
    @output
    @render.table
    def tab_table_tickets():
        df_cli, df_chamados, _ = get_sla_raw()
        if df_chamados.empty: return pd.DataFrame()
        clis = list(input.tab_clientes()) if input.tab_clientes() else None
        cats = list(input.tab_categorias()) if input.tab_categorias() else None
        cons = list(input.tab_consultores()) if input.tab_consultores() else None
        query = input.tab_search().strip()
        df_f = filter_chamados(df_chamados, clientes=clis, categorias=cats, consultores=cons)
        tickets = get_chamados_table(df_f, search_query=query if query else None)
        if not tickets: return pd.DataFrame()
        df_t = pd.DataFrame(tickets)[["ticket_id", "nome_cliente", "titulo", "categoria", "prioridade", "status", "consultor", "horas_consumidas", "data_abertura", "status_sla_geral"]]
        df_t.columns = ["ID", "Cliente", "Título", "Categoria", "Prioridade", "Status", "Consultor", "Horas", "Abertura", "Status SLA"]
        return df_t

app = App(app_ui, server)
