import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.crm import router as crm_router
from routers.sla import router as sla_router

app = FastAPI(
    title="Hub Executivo Unificado API (CRM + SLA Analytics)",
    description="API FastAPI em Python com endpoints dedicados para Gestão de CRM e Acompanhamento de SLA / Contratos.",
    version="1.0.0"
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(crm_router)
app.include_router(sla_router)

@app.get("/", summary="Root Endpoint")
def read_root():
    return {
        "status": "online",
        "service": "Hub Executivo Unificado API (CRM & SLA)",
        "docs_url": "http://localhost:8001/docs",
        "port": 8001
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
