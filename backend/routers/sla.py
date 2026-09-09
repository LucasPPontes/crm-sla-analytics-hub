from typing import List, Optional
from fastapi import APIRouter, Query
from services.sla_service import (
    load_raw_data,
    get_options,
    filter_chamados,
    get_executiva_metrics,
    get_sla_metrics,
    get_contratos_metrics,
    get_equipe_metrics,
    get_chamados_table
)

router = APIRouter(prefix="/api", tags=["SLA & Contratos"])

@router.get("/health", summary="Health check endpoint")
def health_check():
    return {"status": "ok", "message": "FastAPI SLA & CRM Backend is running"}

@router.get("/options", summary="Filtros e opções disponíveis")
def read_options():
    return get_options()

@router.get("/dashboard/executiva", summary="Métricas da Visão Executiva de SLA")
def read_executiva_dashboard(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    clientes: Optional[List[str]] = Query(None),
    prioridades: Optional[List[str]] = Query(None),
    categorias: Optional[List[str]] = Query(None),
    consultores: Optional[List[str]] = Query(None),
    status_sla: Optional[str] = Query("Todos")
):
    df_clientes, df_chamados, _ = load_raw_data()
    df_filtered = filter_chamados(
        df_chamados, start_date, end_date, clientes, prioridades, categorias, consultores, status_sla
    )
    return get_executiva_metrics(df_filtered, df_clientes)

@router.get("/dashboard/sla", summary="Métricas de Gestão de SLA e Prazos")
def read_sla_dashboard(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    clientes: Optional[List[str]] = Query(None),
    prioridades: Optional[List[str]] = Query(None),
    categorias: Optional[List[str]] = Query(None),
    consultores: Optional[List[str]] = Query(None),
    status_sla: Optional[str] = Query("Todos")
):
    _, df_chamados, _ = load_raw_data()
    df_filtered = filter_chamados(
        df_chamados, start_date, end_date, clientes, prioridades, categorias, consultores, status_sla
    )
    return get_sla_metrics(df_filtered)

@router.get("/dashboard/contratos", summary="Métricas de Contratos e Burn Rate de Horas")
def read_contratos_dashboard(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    clientes: Optional[List[str]] = Query(None),
    prioridades: Optional[List[str]] = Query(None),
    categorias: Optional[List[str]] = Query(None),
    consultores: Optional[List[str]] = Query(None),
    status_sla: Optional[str] = Query("Todos")
):
    df_clientes, df_chamados, df_historico = load_raw_data()
    df_filtered = filter_chamados(
        df_chamados, start_date, end_date, clientes, prioridades, categorias, consultores, status_sla
    )
    return get_contratos_metrics(df_filtered, df_clientes, df_historico)

@router.get("/dashboard/equipe", summary="Métricas de Produtividade da Equipe")
def read_equipe_dashboard(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    clientes: Optional[List[str]] = Query(None),
    prioridades: Optional[List[str]] = Query(None),
    categorias: Optional[List[str]] = Query(None),
    consultores: Optional[List[str]] = Query(None),
    status_sla: Optional[str] = Query("Todos")
):
    _, df_chamados, _ = load_raw_data()
    df_filtered = filter_chamados(
        df_chamados, start_date, end_date, clientes, prioridades, categorias, consultores, status_sla
    )
    return get_equipe_metrics(df_filtered)

@router.get("/dashboard/chamados", summary="Tabela Geral e Filtro de Chamados")
def read_chamados_table(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    clientes: Optional[List[str]] = Query(None),
    prioridades: Optional[List[str]] = Query(None),
    categorias: Optional[List[str]] = Query(None),
    consultores: Optional[List[str]] = Query(None),
    status_sla: Optional[str] = Query("Todos"),
    search: Optional[str] = Query(None)
):
    _, df_chamados, _ = load_raw_data()
    df_filtered = filter_chamados(
        df_chamados, start_date, end_date, clientes, prioridades, categorias, consultores, status_sla
    )
    return get_chamados_table(df_filtered, search)
