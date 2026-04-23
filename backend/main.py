"""
Main FastAPI application for AI Boss Decision Engine.
Multi-agent decision support system with LLM integration.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from config import get_settings
from db import DatabaseService
from agents import ManagerAgent, detect_intent

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="Multi-agent decision support system for strategic business questions",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseService()
manager = ManagerAgent(db)


# ── Request / Response Models ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    query: str
    context: Optional[str] = None
    submitted_by: Optional[str] = None


class AnalyzeResponse(BaseModel):
    case_id: Optional[int] = None
    query: str
    agents_invoked: List[str]
    agent_insights: List[Dict[str, Any]]
    conservative_view: Dict[str, str]
    aggressive_view: Dict[str, str]
    final_decision: Dict[str, Any]


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": f"{settings.app_name} API",
        "version": settings.api_version,
    }


@app.get("/api/health")
async def health_check():
    try:
        db.client.table('department').select('count').execute()
        return {"status": "healthy", "database": "connected", "supabase": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/api/employees/{employee_id}")
async def get_employee(employee_id: int):
    try:
        employee = await db.get_employee(employee_id)
        hr_records = await db.get_employee_hr_records(employee_id)
        sales_records = await db.get_employee_sales_records(employee_id)
        return {"employee": employee, "hr_records": hr_records, "sales_records": sales_records}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Employee not found: {str(e)}")


@app.get("/api/cases/{case_id}")
async def get_case(case_id: int):
    try:
        evidence = await db.get_case_evidence(case_id)
        decision = await db.get_decision_output(case_id)
        return {"case_id": case_id, "evidence": evidence, "decision": decision}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Case not found: {str(e)}")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_query(request: AnalyzeRequest):
    """
    Main decision engine endpoint.
    Detects intent → selects agents → runs analysis in parallel → manager synthesis.
    """
    # 1. Detect intent: which agents + entity context
    try:
        intent = await detect_intent(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent detection failed: {str(e)}")

    # 2. Create decision case in DB
    case_id = None
    try:
        case = await db.create_decision_case(
            question=request.query,
            context=request.context,
            target_type=intent.get("target_type"),
            target_id=intent.get("target_id"),
            submitted_by=request.submitted_by,
        )
        case_id = case.get("case_id")
    except Exception:
        pass  # non-fatal: proceed without persisting case

    # 3. Run multi-agent pipeline via Manager
    try:
        result = await manager.orchestrate(request.query, intent)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent pipeline failed: {str(e)}")

    # 4. Persist decision output
    if case_id:
        try:
            fd = result.get("final_decision", {})
            await db.save_decision_output(
                case_id=case_id,
                recommendation=fd.get("verdict", ""),
                risk_level=fd.get("risk_level", "Medium"),
                confidence_score=fd.get("confidence_score", 0) / 100,
                rationale=fd.get("reasoning", ""),
                conservative_view=str(result.get("conservative_view", {})),
                aggressive_view=str(result.get("aggressive_view", {})),
                manager_persona="balanced",
            )
        except Exception:
            pass

    return AnalyzeResponse(
        case_id=case_id,
        query=request.query,
        agents_invoked=intent.get("agents", []),
        agent_insights=result.get("agent_insights", []),
        conservative_view=result.get("conservative_view", {}),
        aggressive_view=result.get("aggressive_view", {}),
        final_decision=result.get("final_decision", {}),
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )
