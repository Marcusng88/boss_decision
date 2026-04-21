"""
Main FastAPI application for AI Boss Decision Engine.
Multi-agent decision support system with LangChain integration.
"""
import asyncio
import json
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Optional
import uvicorn

from config import get_settings
from db import DatabaseService

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="Multi-agent decision support system for strategic business questions"
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database service
db = DatabaseService()


# ============================================
# Request/Response Models
# ============================================

class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint."""
    query: str
    context: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    submitted_by: Optional[str] = None


class SimulatorRequest(BaseModel):
    """Request model for simulator graph execution."""

    query: str
    structured_data: Optional[dict[str, Any]] = None
    documents: Optional[list[str]] = None
    business_context: Optional[dict[str, Any]] = None


class EmployeeResponse(BaseModel):
    """Response model for employee endpoint."""
    employee: dict
    hr_records: list[dict]
    sales_records: list[dict]


def _ensure_simulator_import_path() -> None:
    simulator_root = Path(__file__).resolve().parent / "simulator_agent_umh26"
    simulator_root_str = str(simulator_root)
    if simulator_root_str not in sys.path:
        sys.path.insert(0, simulator_root_str)


def _get_simulator_agent():
    _ensure_simulator_import_path()
    from simulator_agent_umh26.src import agent as simulator_agent

    return simulator_agent


def _build_simulator_initial_state(request: SimulatorRequest) -> dict[str, Any]:
    return {
        "query": request.query,
        "structured_data": request.structured_data or {},
        "documents": request.documents or [],
        "business_context": request.business_context or {},
        "persona_results": [],
        "persona_stream_events": [],
        "scenario_branches": [],
    }


def _ndjson_line(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=str) + "\n"


def _extract_token_text(raw_content: Any) -> str:
    if isinstance(raw_content, str):
        return raw_content

    if isinstance(raw_content, list):
        parts: list[str] = []
        for item in raw_content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
        return "".join(parts)

    return ""


def _safe_json_payload(data: Any) -> Any:
    try:
        json.dumps(data, default=str)
        return data
    except Exception:
        return str(data)


# ============================================
# Routes
# ============================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": f"{settings.app_name} API",
        "version": settings.api_version
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check with database connectivity."""
    try:
        # Test database connection
        supabase = db.client
        response = supabase.table('department').select('count').execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "supabase": "ok"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/api/employees/{employee_id}")
async def get_employee(employee_id: int):
    """Get employee profile with related records."""
    try:
        employee = await db.get_employee(employee_id)
        hr_records = await db.get_employee_hr_records(employee_id)
        sales_records = await db.get_employee_sales_records(employee_id)
        
        return {
            "employee": employee,
            "hr_records": hr_records,
            "sales_records": sales_records
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Employee not found: {str(e)}")


@app.get("/api/cases/{case_id}")
async def get_case(case_id: int):
    """Get decision case with evidence and output."""
    try:
        evidence = await db.get_case_evidence(case_id)
        decision = await db.get_decision_output(case_id)
        
        return {
            "case_id": case_id,
            "evidence": evidence,
            "decision": decision
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Case not found: {str(e)}")


@app.post("/api/analyze")
async def analyze_query(request: AnalyzeRequest):
    """
    Main decision engine endpoint.
    Analyzes a business question using multi-agent system.
    
    TODO: Implement full agent orchestration (see agents/ folder)
    """
    try:
        # Create decision case
        case = await db.create_decision_case(
            question=request.query,
            context=request.context,
            target_type=request.target_type,
            target_id=request.target_id,
            submitted_by=request.submitted_by
        )
        
        # TODO: Implement multi-agent pipeline
        # 1. Evidence retrieval (retrieve relevant records)
        # 2. Agent analysis (HR, Sales, Legal, Finance, Marketing, Supply Chain)
        # 3. Manager synthesis (aggregate agent outputs)
        # 4. Save decision output
        
        # For now, return case ID with placeholder
        return {
            "status": "processing",
            "case_id": case['case_id'],
            "message": "Decision case created. Multi-agent pipeline not yet implemented.",
            "query": request.query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/simulator/run")
async def run_simulator(request: SimulatorRequest):
    """
    Execute simulator graph and return final result in one response.
    """
    try:
        simulator_agent = _get_simulator_agent()
        initial_state = _build_simulator_initial_state(request)
        result = await asyncio.to_thread(simulator_agent.invoke, initial_state)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulator run failed: {str(e)}")


@app.post("/api/simulator/stream")
async def stream_simulator(request: SimulatorRequest):
    """
    Stream simulator updates and tokens as NDJSON.
    """
    simulator_agent = _get_simulator_agent()
    initial_state = _build_simulator_initial_state(request)

    async def event_stream():
        latest_values: dict[str, Any] | None = None
        try:
            yield _ndjson_line({"type": "status", "message": "Simulator stream started."})
            async for part in simulator_agent.astream(
                initial_state,
                stream_mode=["updates", "messages", "values"],
                version="v2",
            ):
                part_type = part.get("type")
                if part_type == "updates":
                    updates = part.get("data", {})
                    nodes = list(updates.keys()) if isinstance(updates, dict) else []
                    if nodes:
                        yield _ndjson_line(
                            {
                                "type": "update",
                                "nodes": nodes,
                                "updates": _safe_json_payload(updates),
                            }
                        )
                elif part_type == "messages":
                    data = part.get("data")
                    if isinstance(data, (tuple, list)) and data:
                        message_chunk = data[0]
                        metadata = data[1] if len(data) > 1 and isinstance(data[1], dict) else {}
                        raw_content = getattr(message_chunk, "content", "")
                        token = _extract_token_text(raw_content)
                        if token:
                            yield _ndjson_line(
                                {
                                    "type": "token",
                                    "text": token,
                                    "node": metadata.get("langgraph_node"),
                                    "meta": _safe_json_payload(metadata),
                                }
                            )
                elif part_type == "values":
                    values = part.get("data")
                    if isinstance(values, dict):
                        latest_values = values

            if latest_values is not None:
                yield _ndjson_line(
                    {"type": "final", "response": latest_values.get("response"), "state": latest_values}
                )
            else:
                yield _ndjson_line({"type": "final", "response": "Simulation completed."})
        except Exception as e:
            yield _ndjson_line({"type": "error", "error": str(e)})
        finally:
            yield _ndjson_line({"type": "done"})

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True  # Auto-reload on code changes (development only)
    )
