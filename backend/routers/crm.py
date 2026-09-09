from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from services.crm_service import load_crm_data

router = APIRouter(prefix="/api/v1", tags=["CRM"])

# Pydantic Response Schemas
class MRRResponse(BaseModel):
    total_mrr: float
    total_arr: float
    mom_growth: float

class LTVCACResponse(BaseModel):
    avg_ltv: float
    avg_cac: float
    ltv_cac_ratio: float

class ChurnRateResponse(BaseModel):
    churn_rate: float
    total_active_customers: int
    total_churned_customers: int
    target_churn_rate: float

class NPSResponse(BaseModel):
    avg_nps: float
    avg_health_score: float
    promoters_count: int
    passives_count: int
    detractors_count: int

class WinRateResponse(BaseModel):
    win_rate: float
    total_won_deals: int
    total_closed_deals: int

class PipelineResponse(BaseModel):
    total_pipeline_value: float
    weighted_pipeline_value: float
    active_deals_count: int

class SalesCycleResponse(BaseModel):
    avg_sales_cycle_days: int

# 1. GET /api/v1/kpis/mrr
@router.get("/kpis/mrr", response_model=MRRResponse, summary="Indicador de Receita Recorrente (MRR / ARR)")
def get_mrr_kpi():
    data = load_crm_data()
    active_customers = [c for c in data.get("customers", []) if c.get("status") in ["Ativo", "Em Risco"]]
    total_mrr = sum(c.get("mrr", 0) for c in active_customers)
    total_arr = total_mrr * 12
    return MRRResponse(
        total_mrr=total_mrr,
        total_arr=total_arr,
        mom_growth=8.4
    )

# 2. GET /api/v1/kpis/ltv-cac
@router.get("/kpis/ltv-cac", response_model=LTVCACResponse, summary="Indicador de LTV & CAC Médio")
def get_ltv_cac_kpi():
    data = load_crm_data()
    active_customers = [c for c in data.get("customers", []) if c.get("status") in ["Ativo", "Em Risco"]]
    count = len(active_customers)
    avg_ltv = sum(c.get("ltv", 0) for c in active_customers) / count if count > 0 else 0.0
    avg_cac = sum(c.get("cac", 0) for c in active_customers) / count if count > 0 else 0.0
    ratio = avg_ltv / avg_cac if avg_cac > 0 else 0.0
    return LTVCACResponse(
        avg_ltv=round(avg_ltv, 2),
        avg_cac=round(avg_cac, 2),
        ltv_cac_ratio=round(ratio, 2)
    )

# 3. GET /api/v1/kpis/churn-rate
@router.get("/kpis/churn-rate", response_model=ChurnRateResponse, summary="Indicador de Churn Rate")
def get_churn_kpi():
    data = load_crm_data()
    customers = data.get("customers", [])
    total = len(customers)
    churned = len([c for c in customers if c.get("status") == "Churn"])
    active = len([c for c in customers if c.get("status") in ["Ativo", "Em Risco"]])
    rate = (churned / total * 100) if total > 0 else 0.0
    return ChurnRateResponse(
        churn_rate=round(rate, 2),
        total_active_customers=active,
        total_churned_customers=churned,
        target_churn_rate=3.0
    )

# 4. GET /api/v1/kpis/nps
@router.get("/kpis/nps", response_model=NPSResponse, summary="Indicador de NPS & Health Score")
def get_nps_kpi():
    data = load_crm_data()
    active = [c for c in data.get("customers", []) if c.get("status") != "Churn"]
    count = len(active)
    avg_nps = sum(c.get("nps", 0) for c in active) / count if count > 0 else 0.0
    avg_health = sum(c.get("healthScore", 0) for c in active) / count if count > 0 else 0.0
    
    promoters = len([c for c in active if c.get("nps", 0) >= 9])
    passives = len([c for c in active if 7 <= c.get("nps", 0) <= 8])
    detractors = len([c for c in active if c.get("nps", 0) <= 6])

    return NPSResponse(
        avg_nps=round(avg_nps, 1),
        avg_health_score=round(avg_health, 1),
        promoters_count=promoters,
        passives_count=passives,
        detractors_count=detractors
    )

# 5. GET /api/v1/kpis/win-rate
@router.get("/kpis/win-rate", response_model=WinRateResponse, summary="Indicador de Taxa de Conversão (Win Rate)")
def get_win_rate_kpi():
    data = load_crm_data()
    deals = data.get("deals", [])
    won = len([d for d in deals if d.get("stage") == "Fechado Ganho"])
    lost = len([d for d in deals if d.get("stage") == "Fechado Perdido"])
    closed = won + lost
    rate = (won / closed * 100) if closed > 0 else 0.0
    return WinRateResponse(
        win_rate=round(rate, 1),
        total_won_deals=won,
        total_closed_deals=closed
    )

# 6. GET /api/v1/kpis/pipeline
@router.get("/kpis/pipeline", response_model=PipelineResponse, summary="Indicador de Valor do Pipeline Ativo")
def get_pipeline_kpi():
    data = load_crm_data()
    deals = data.get("deals", [])
    active_deals = [d for d in deals if d.get("stage") not in ["Fechado Ganho", "Fechado Perdido"]]
    total_val = sum(d.get("value", 0) for d in active_deals)
    weighted_val = sum(d.get("value", 0) * (d.get("probability", 0) / 100.0) for d in active_deals)
    return PipelineResponse(
        total_pipeline_value=total_val,
        weighted_pipeline_value=weighted_val,
        active_deals_count=len(active_deals)
    )

# 7. GET /api/v1/kpis/sales-cycle
@router.get("/kpis/sales-cycle", response_model=SalesCycleResponse, summary="Indicador de Tempo Médio de Fechamento")
def get_sales_cycle_kpi():
    return SalesCycleResponse(avg_sales_cycle_days=34)

# 8. GET /api/v1/analytics/mrr-evolution
@router.get("/analytics/mrr-evolution", summary="Evolução Mensal do MRR & Churn")
def get_mrr_evolution():
    return [
        {"month": "Ago/25", "mrr": 820000, "churn": 18000},
        {"month": "Set/25", "mrr": 890000, "churn": 15000},
        {"month": "Out/25", "mrr": 960000, "churn": 22000},
        {"month": "Nov/25", "mrr": 1040000, "churn": 19000},
        {"month": "Dez/25", "mrr": 1120000, "churn": 24000},
        {"month": "Jan/26", "mrr": 1210000, "churn": 20000},
        {"month": "Fev/26", "mrr": 1290000, "churn": 17000},
        {"month": "Mar/26", "mrr": 1380000, "churn": 21000},
        {"month": "Abr/26", "mrr": 1470000, "churn": 25000},
        {"month": "Mai/26", "mrr": 1560000, "churn": 19000},
        {"month": "Jun/26", "mrr": 1650000, "churn": 23000},
        {"month": "Jul/26", "mrr": 1780000, "churn": 18000},
    ]

# 9. GET /api/v1/analytics/pipeline-stages
@router.get("/analytics/pipeline-stages", summary="Distribuição por Estágio do Funil")
def get_pipeline_stages():
    data = load_crm_data()
    deals = data.get("deals", [])
    stages = ["Prospecção", "Qualificação", "Proposta", "Negociação", "Fechado Ganho", "Fechado Perdido"]
    result = []
    for stage in stages:
        stage_deals = [d for d in deals if d.get("stage") == stage]
        result.append({
            "stage": stage,
            "count": len(stage_deals),
            "total_value": sum(d.get("value", 0) for d in stage_deals)
        })
    return result

# 10. GET /api/v1/analytics/cohort-retention
@router.get("/analytics/cohort-retention", summary="Matriz de Retenção por Cohort")
def get_cohort_retention():
    return [
        {"cohortMonth": "2025-08", "cohortSize": 45, "retentionByMonth": [100, 93, 88, 84, 82, 80, 78, 76, 75, 74, 73, 72]},
        {"cohortMonth": "2025-09", "cohortSize": 48, "retentionByMonth": [100, 95, 91, 87, 85, 83, 81, 80, 78, 77, 76]},
        {"cohortMonth": "2025-10", "cohortSize": 52, "retentionByMonth": [100, 94, 90, 88, 86, 84, 83, 81, 80, 79]},
        {"cohortMonth": "2025-11", "cohortSize": 50, "retentionByMonth": [100, 96, 92, 89, 87, 85, 84, 82, 81]},
        {"cohortMonth": "2025-12", "cohortSize": 55, "retentionByMonth": [100, 92, 89, 86, 84, 82, 81, 80]},
        {"cohortMonth": "2026-01", "cohortSize": 60, "retentionByMonth": [100, 95, 93, 90, 88, 87, 85]},
        {"cohortMonth": "2026-02", "cohortSize": 58, "retentionByMonth": [100, 94, 91, 89, 87, 86]},
        {"cohortMonth": "2026-03", "cohortSize": 62, "retentionByMonth": [100, 96, 94, 91, 89]},
        {"cohortMonth": "2026-04", "cohortSize": 65, "retentionByMonth": [100, 95, 92, 90]},
        {"cohortMonth": "2026-05", "cohortSize": 68, "retentionByMonth": [100, 97, 94]},
        {"cohortMonth": "2026-06", "cohortSize": 70, "retentionByMonth": [100, 96]},
        {"cohortMonth": "2026-07", "cohortSize": 72, "retentionByMonth": [100]}
    ]

# 11. GET /api/v1/customers
@router.get("/customers", summary="Listagem Geral de Clientes")
def get_customers(status: Optional[str] = None, search: Optional[str] = None):
    data = load_crm_data()
    customers = data.get("customers", [])
    if status and status != "all":
        customers = [c for c in customers if c.get("status") == status]
    if search:
        query = search.lower()
        customers = [c for c in customers if query in c.get("name", "").lower() or query in c.get("company", "").lower()]
    return customers

# 12. GET /api/v1/customers/{customer_id}
@router.get("/customers/{customer_id}", summary="Detalhes de Cliente")
def get_customer_by_id(customer_id: str):
    data = load_crm_data()
    customers = data.get("customers", [])
    customer = next((c for c in customers if c.get("id") == customer_id), None)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    interactions = [i for i in data.get("interactions", []) if i.get("customerId") == customer_id]
    deals = [d for d in data.get("deals", []) if d.get("customerId") == customer_id]
    return {
        "customer": customer,
        "interactions": interactions,
        "deals": deals
    }

# 13. GET /api/v1/deals
@router.get("/deals", summary="Listagem de Negócios")
def get_deals(stage: Optional[str] = None):
    data = load_crm_data()
    deals = data.get("deals", [])
    if stage and stage != "all":
        deals = [d for d in deals if d.get("stage") == stage]
    return deals

# 14. GET /api/v1/interactions
@router.get("/interactions", summary="Feed de Interações")
def get_interactions(limit: int = Query(default=50, ge=1, le=100)):
    data = load_crm_data()
    interactions = data.get("interactions", [])
    return interactions[:limit]
