import os
import pandas as pd
import numpy as np
from typing import List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def load_raw_data():
    clientes_path = os.path.join(DATA_DIR, "clientes.csv")
    chamados_path = os.path.join(DATA_DIR, "chamados.csv")
    historico_path = os.path.join(DATA_DIR, "historico_consumo.csv")

    if not os.path.exists(clientes_path) or not os.path.exists(chamados_path):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_clientes = pd.read_csv(clientes_path, encoding="utf-8")
    df_chamados = pd.read_csv(chamados_path, encoding="utf-8")
    df_historico = pd.read_csv(historico_path, encoding="utf-8") if os.path.exists(historico_path) else pd.DataFrame()

    # Dates
    df_chamados["data_abertura_dt"] = pd.to_datetime(df_chamados["data_abertura"])
    df_chamados["data_primeira_resposta_dt"] = pd.to_datetime(df_chamados["data_primeira_resposta"])
    df_chamados["data_solucao_dt"] = pd.to_datetime(df_chamados["data_solucao"])

    # Hours calculation
    df_chamados["tempo_resposta_hs"] = np.round(
        (df_chamados["data_primeira_resposta_dt"] - df_chamados["data_abertura_dt"]).dt.total_seconds() / 3600.0, 2
    )

    df_chamados["tempo_solucao_hs"] = np.where(
        df_chamados["data_solucao_dt"].notnull(),
        np.round((df_chamados["data_solucao_dt"] - df_chamados["data_abertura_dt"]).dt.total_seconds() / 3600.0, 2),
        np.nan
    )

    # Merge client info
    df_chamados = df_chamados.merge(
        df_clientes[["cliente_id", "nome_cliente", "segmento", "horas_contratadas_mes", "valor_hora_adicional", "gerente_conta"]],
        on="cliente_id",
        how="left"
    )

    df_chamados["mes_ano"] = df_chamados["data_abertura_dt"].dt.strftime("%Y-%m")
    df_chamados["data_apenas"] = df_chamados["data_abertura_dt"].dt.strftime("%Y-%m-%d")

    def define_status_sla(row):
        if row["status"] == "Fechado":
            if row["cumpre_sla_solucao"] and row["cumpre_sla_resposta"]:
                return "SLA Cumprido (100%)"
            elif not row["cumpre_sla_solucao"]:
                return "SLA Solução Violado"
            else:
                return "SLA Resposta Violado"
        else:
            return "Em Atendimento"

    df_chamados["status_sla_geral"] = df_chamados.apply(define_status_sla, axis=1)

    return df_clientes, df_chamados, df_historico

def get_options():
    df_clientes, df_chamados, _ = load_raw_data()
    if df_chamados.empty:
        return {}

    clientes = sorted(df_clientes["nome_cliente"].unique().tolist())
    prioridades = ["Crítica", "Alta", "Média", "Baixa"]
    categorias = sorted(df_chamados["categoria"].unique().tolist())
    consultores = sorted(df_chamados["consultor"].unique().tolist())
    min_date = df_chamados["data_apenas"].min()
    max_date = df_chamados["data_apenas"].max()

    return {
        "clientes": clientes,
        "prioridades": prioridades,
        "categorias": categorias,
        "consultores": consultores,
        "min_date": min_date,
        "max_date": max_date
    }

def filter_chamados(
    df_chamados: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    clientes: Optional[List[str]] = None,
    prioridades: Optional[List[str]] = None,
    categorias: Optional[List[str]] = None,
    consultores: Optional[List[str]] = None,
    status_sla: Optional[str] = "Todos"
):
    df_filtered = df_chamados.copy()
    if df_filtered.empty:
        return df_filtered

    if start_date:
        df_filtered = df_filtered[df_filtered["data_apenas"] >= start_date]
    if end_date:
        df_filtered = df_filtered[df_filtered["data_apenas"] <= end_date]

    if clientes:
        df_filtered = df_filtered[df_filtered["nome_cliente"].isin(clientes)]
    if prioridades:
        df_filtered = df_filtered[df_filtered["prioridade"].isin(prioridades)]
    if categorias:
        df_filtered = df_filtered[df_filtered["categoria"].isin(categorias)]
    if consultores:
        df_filtered = df_filtered[df_filtered["consultor"].isin(consultores)]

    if status_sla and status_sla != "Todos":
        if status_sla == "Dentro do SLA":
            df_filtered = df_filtered[df_filtered["cumpre_sla_solucao"] == True]
        elif status_sla == "Fora do SLA":
            df_filtered = df_filtered[df_filtered["cumpre_sla_solucao"] == False]

    return df_filtered

def get_executiva_metrics(df_filtered: pd.DataFrame, df_clientes: pd.DataFrame):
    total_chamados = len(df_filtered)
    chamados_fechados = df_filtered[df_filtered["status"] == "Fechado"] if not df_filtered.empty else pd.DataFrame()
    
    sla_solucao_pct = (float(chamados_fechados["cumpre_sla_solucao"].sum()) / len(chamados_fechados) * 100) if len(chamados_fechados) > 0 else 0.0
    sla_resposta_pct = (float(df_filtered["cumpre_sla_resposta"].sum()) / total_chamados * 100) if total_chamados > 0 else 0.0
    total_horas_consumidas = float(df_filtered["horas_consumidas"].sum()) if total_chamados > 0 else 0.0

    if not df_filtered.empty:
        horas_por_cli = df_filtered.groupby("cliente_id")["horas_consumidas"].sum().reset_index()
        horas_por_cli = horas_por_cli.merge(df_clientes[["cliente_id", "horas_contratadas_mes", "valor_hora_adicional"]], on="cliente_id", how="left")
        horas_por_cli["excedente"] = (horas_por_cli["horas_consumidas"] - horas_por_cli["horas_contratadas_mes"]).clip(lower=0)
        horas_por_cli["faturamento_extra"] = horas_por_cli["excedente"] * horas_por_cli["valor_hora_adicional"]
        total_faturamento_extra = float(horas_por_cli["faturamento_extra"].sum())
        total_horas_excedentes = float(horas_por_cli["excedente"].sum())
    else:
        total_faturamento_extra = 0.0
        total_horas_excedentes = 0.0

    evolucao_mensal = []
    if not df_filtered.empty:
        df_monthly = df_filtered.groupby("mes_ano").agg(
            total_atendidos=('ticket_id', 'count'),
            sla_solucao_cumprido=('cumpre_sla_solucao', lambda x: int((x == True).sum())),
            sla_solucao_total=('cumpre_sla_solucao', 'count'),
            horas=('horas_consumidas', 'sum')
        ).reset_index()

        df_monthly["taxa_sla"] = np.round((df_monthly["sla_solucao_cumprido"] / df_monthly["sla_solucao_total"]) * 100, 1)

        for _, row in df_monthly.iterrows():
            evolucao_mensal.append({
                "mes_ano": str(row["mes_ano"]),
                "total_atendidos": int(row["total_atendidos"]),
                "sla_solucao_cumprido": int(row["sla_solucao_cumprido"]),
                "sla_solucao_total": int(row["sla_solucao_total"]),
                "taxa_sla": float(row["taxa_sla"]),
                "horas": float(np.round(row["horas"], 1))
            })

    categorias_distribuicao = []
    if not df_filtered.empty:
        cat_counts = df_filtered["categoria"].value_counts().reset_index()
        cat_counts.columns = ["categoria", "quantidade"]
        for _, row in cat_counts.iterrows():
            categorias_distribuicao.append({
                "categoria": str(row["categoria"]),
                "quantidade": int(row["quantidade"])
            })

    consumo_por_cliente = []
    if not df_filtered.empty:
        df_cli_summary = df_filtered.groupby("nome_cliente").agg(
            horas_consumidas=('horas_consumidas', 'sum'),
            horas_contratadas=('horas_contratadas_mes', 'first')
        ).reset_index()
        df_cli_summary["estouro"] = df_cli_summary["horas_consumidas"] > df_cli_summary["horas_contratadas"]
        df_cli_summary = df_cli_summary.sort_values(by="horas_consumidas", ascending=True)

        for _, row in df_cli_summary.iterrows():
            consumo_por_cliente.append({
                "nome_cliente": str(row["nome_cliente"]),
                "horas_consumidas": float(np.round(row["horas_consumidas"], 1)),
                "horas_contratadas": float(row["horas_contratadas"]),
                "estouro": bool(row["estouro"])
            })

    return {
        "total_chamados": total_chamados,
        "chamados_resolvidos": len(chamados_fechados),
        "sla_solucao_pct": round(sla_solucao_pct, 1),
        "sla_resposta_pct": round(sla_resposta_pct, 1),
        "total_horas_consumidas": round(total_horas_consumidas, 1),
        "total_faturamento_extra": round(total_faturamento_extra, 2),
        "total_horas_excedentes": round(total_horas_excedentes, 1),
        "evolucao_mensal": evolucao_mensal,
        "categorias_distribuicao": categorias_distribuicao,
        "consumo_por_cliente": consumo_por_cliente
    }

def get_sla_metrics(df_filtered: pd.DataFrame):
    if df_filtered.empty:
        return {
            "mtta_medio": 0.0,
            "mttr_medio": 0.0,
            "violados_solucao_count": 0,
            "violados_solucao_pct": 0.0,
            "violados_resposta_count": 0,
            "violados_resposta_pct": 0.0,
            "sla_por_prioridade": [],
            "tempo_medio_vs_alvo": [],
            "chamados_estouro": []
        }

    total = len(df_filtered)
    mtta_medio = float(df_filtered["tempo_resposta_hs"].mean()) if total > 0 else 0.0
    mtt_sol = float(df_filtered["tempo_solucao_hs"].dropna().mean()) if total > 0 else 0.0

    violados_sol = df_filtered[df_filtered["cumpre_sla_solucao"] == False]
    violados_resp = df_filtered[df_filtered["cumpre_sla_resposta"] == False]

    violados_sol_count = len(violados_sol)
    violados_resp_count = len(violados_resp)

    violados_sol_pct = (violados_sol_count / total * 100) if total > 0 else 0.0
    violados_resp_pct = (violados_resp_count / total * 100) if total > 0 else 0.0

    df_prio_sla = df_filtered.groupby(["prioridade", "cumpre_sla_solucao"]).size().unstack(fill_value=0).reset_index()
    if True not in df_prio_sla.columns: df_prio_sla[True] = 0
    if False not in df_prio_sla.columns: df_prio_sla[False] = 0

    sla_por_prioridade = []
    for _, row in df_prio_sla.iterrows():
        sla_por_prioridade.append({
            "prioridade": str(row["prioridade"]),
            "cumprido": int(row[True]),
            "violado": int(row[False])
        })

    df_tempo_prio = df_filtered.groupby("prioridade").agg(
        tempo_real=('tempo_solucao_hs', 'mean'),
        sla_alvo=('sla_solucao_alvo_hs', 'first')
    ).reset_index()

    tempo_medio_vs_alvo = []
    for _, row in df_tempo_prio.iterrows():
        tempo_medio_vs_alvo.append({
            "prioridade": str(row["prioridade"]),
            "tempo_real": float(round(row["tempo_real"], 1)) if pd.notnull(row["tempo_real"]) else 0.0,
            "sla_alvo": float(row["sla_alvo"])
        })

    chamados_estouro = []
    df_breached_details = violados_sol.copy()
    if not df_breached_details.empty:
        df_breached_details["atraso_hs"] = df_breached_details["tempo_solucao_hs"] - df_breached_details["sla_solucao_alvo_hs"]
        df_breached_details = df_breached_details.sort_values(by="atraso_hs", ascending=False)

        for _, row in df_breached_details.iterrows():
            chamados_estouro.append({
                "ticket_id": str(row["ticket_id"]),
                "nome_cliente": str(row["nome_cliente"]),
                "titulo": str(row["titulo"]),
                "prioridade": str(row["prioridade"]),
                "categoria": str(row["categoria"]),
                "consultor": str(row["consultor"]),
                "sla_solucao_alvo_hs": float(row["sla_solucao_alvo_hs"]),
                "tempo_solucao_hs": float(row["tempo_solucao_hs"]) if pd.notnull(row["tempo_solucao_hs"]) else 0.0,
                "atraso_hs": float(round(row["atraso_hs"], 1))
            })

    return {
        "mtta_medio": round(mtta_medio, 2),
        "mttr_medio": round(mtt_sol, 2),
        "violados_solucao_count": violados_sol_count,
        "violados_solucao_pct": round(violados_sol_pct, 1),
        "violados_resposta_count": violados_resp_count,
        "violados_resposta_pct": round(violados_resp_pct, 1),
        "sla_por_prioridade": sla_por_prioridade,
        "tempo_medio_vs_alvo": tempo_medio_vs_alvo,
        "chamados_estouro": chamados_estouro
    }

def get_contratos_metrics(df_filtered: pd.DataFrame, df_clientes: pd.DataFrame, df_historico: pd.DataFrame):
    if df_filtered.empty:
        return {
            "total_franquias": 0.0,
            "total_consumido": 0.0,
            "pct_consumo_global": 0.0,
            "clientes_estourados": 0,
            "receita_excedente": 0.0,
            "status_contratos": [],
            "historico_mensal": []
        }

    df_contract_status = df_filtered.groupby(["cliente_id", "nome_cliente", "segmento", "horas_contratadas_mes", "valor_hora_adicional", "gerente_conta"]).agg(
        horas_consumidas=('horas_consumidas', 'sum'),
        total_tickets=('ticket_id', 'count')
    ).reset_index()

    df_contract_status["pct_consumo"] = np.round((df_contract_status["horas_consumidas"] / df_contract_status["horas_contratadas_mes"]) * 100, 1)
    df_contract_status["horas_excedentes"] = (df_contract_status["horas_consumidas"] - df_contract_status["horas_contratadas_mes"]).clip(lower=0)
    df_contract_status["valor_faturar_extra"] = df_contract_status["horas_excedentes"] * df_contract_status["valor_hora_adicional"]

    total_franquias = float(df_contract_status["horas_contratadas_mes"].sum())
    total_consumido = float(df_contract_status["horas_consumidas"].sum())
    pct_consumo_global = round((total_consumido / total_franquias * 100), 1) if total_franquias > 0 else 0.0
    receita_excedente = float(df_contract_status["valor_faturar_extra"].sum())
    clientes_estourados = int((df_contract_status["pct_consumo"] > 100).sum())

    df_display_contracts = df_contract_status.sort_values(by="pct_consumo", ascending=False)

    status_contratos = []
    for _, row in df_display_contracts.iterrows():
        status_contratos.append({
            "cliente_id": str(row["cliente_id"]),
            "nome_cliente": str(row["nome_cliente"]),
            "segmento": str(row["segmento"]),
            "gerente_conta": str(row["gerente_conta"]),
            "horas_contratadas_mes": float(row["horas_contratadas_mes"]),
            "horas_consumidas": float(round(row["horas_consumidas"], 1)),
            "pct_consumo": float(row["pct_consumo"]),
            "horas_excedentes": float(round(row["horas_excedentes"], 1)),
            "valor_hora_adicional": float(row["valor_hora_adicional"]),
            "valor_faturar_extra": float(round(row["valor_faturar_extra"], 2))
        })

    historico_mensal = []
    if not df_historico.empty:
        hist_trend = df_historico.groupby("mes_referencia").agg(
            horas_contratadas=('horas_contratadas', 'sum'),
            horas_consumidas=('horas_consumidas', 'sum'),
            faturamento_extra=('faturamento_extra', 'sum')
        ).reset_index()

        for _, row in hist_trend.iterrows():
            historico_mensal.append({
                "mes_referencia": str(row["mes_referencia"]),
                "horas_contratadas": float(row["horas_contratadas"]),
                "horas_consumidas": float(round(row["horas_consumidas"], 1)),
                "faturamento_extra": float(round(row["faturamento_extra"], 2))
            })

    return {
        "total_franquias": round(total_franquias, 0),
        "total_consumido": round(total_consumido, 1),
        "pct_consumo_global": pct_consumo_global,
        "clientes_estourados": clientes_estourados,
        "receita_excedente": round(receita_excedente, 2),
        "status_contratos": status_contratos,
        "historico_mensal": historico_mensal
    }

def get_equipe_metrics(df_filtered: pd.DataFrame):
    if df_filtered.empty:
        return {
            "destaque_sla": {"consultor": "N/A", "taxa_sla_pct": 0.0},
            "mais_horas": {"consultor": "N/A", "horas_totais": 0.0},
            "media_horas_consultor": 0.0,
            "media_chamados_consultor": 0,
            "horas_por_consultor": [],
            "sla_por_consultor": []
        }

    df_consultores = df_filtered.groupby("consultor").agg(
        total_chamados=('ticket_id', 'count'),
        horas_totais=('horas_consumidas', 'sum'),
        sla_cumprido=('cumpre_sla_solucao', lambda x: int((x == True).sum())),
        sla_total=('cumpre_sla_solucao', 'count'),
        mtt_solucao=('tempo_solucao_hs', 'mean')
    ).reset_index()

    df_consultores["taxa_sla_pct"] = np.round((df_consultores["sla_cumprido"] / df_consultores["sla_total"]) * 100, 1)

    top_sla_row = df_consultores.sort_values(by="taxa_sla_pct", ascending=False).iloc[0]
    top_horas_row = df_consultores.sort_values(by="horas_totais", ascending=False).iloc[0]

    media_horas = float(df_consultores["horas_totais"].mean())
    media_chamados = float(df_consultores["total_chamados"].mean())

    horas_por_consultor = []
    for _, row in df_consultores.sort_values(by="horas_totais", ascending=True).iterrows():
        horas_por_consultor.append({
            "consultor": str(row["consultor"]),
            "horas_totais": float(round(row["horas_totais"], 1))
        })

    sla_por_consultor = []
    for _, row in df_consultores.sort_values(by="taxa_sla_pct", ascending=True).iterrows():
        sla_por_consultor.append({
            "consultor": str(row["consultor"]),
            "taxa_sla_pct": float(row["taxa_sla_pct"])
        })

    return {
        "destaque_sla": {
            "consultor": str(top_sla_row["consultor"]),
            "taxa_sla_pct": float(top_sla_row["taxa_sla_pct"])
        },
        "mais_horas": {
            "consultor": str(top_horas_row["consultor"]),
            "horas_totais": float(round(top_horas_row["horas_totais"], 1))
        },
        "media_horas_consultor": round(media_horas, 1),
        "media_chamados_consultor": round(media_chamados, 0),
        "horas_por_consultor": horas_por_consultor,
        "sla_por_consultor": sla_por_consultor
    }

def get_chamados_table(df_filtered: pd.DataFrame, search_query: Optional[str] = None):
    if df_filtered.empty:
        return []

    df_table = df_filtered.copy()
    if search_query:
        df_table = df_table[
            df_table["titulo"].str.contains(search_query, case=False, na=False) |
            df_table["ticket_id"].str.contains(search_query, case=False, na=False)
        ]

    chamados = []
    for _, row in df_table.iterrows():
        chamados.append({
            "ticket_id": str(row["ticket_id"]),
            "nome_cliente": str(row["nome_cliente"]),
            "titulo": str(row["titulo"]),
            "categoria": str(row["categoria"]),
            "prioridade": str(row["prioridade"]),
            "status": str(row["status"]),
            "consultor": str(row["consultor"]),
            "horas_consumidas": float(round(row["horas_consumidas"], 1)),
            "data_abertura": str(row["data_abertura"]),
            "status_sla_geral": str(row["status_sla_geral"])
        })

    return chamados
