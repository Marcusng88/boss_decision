"""
Main FastAPI application for AI Boss Decision Engine.
Multi-agent decision support system with LangChain integration.
"""
import asyncio
import json
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import Field
from typing import Any, Optional
import uvicorn
import tempfile
import os
from datetime import datetime

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


class DeepSimulatorRequest(BaseModel):
    """Request model for deep 2D simulator execution."""

    query: str
    max_ticks: int = 5
    seed: Optional[int] = None
    scenario_id: str = "pricing_war_v1"
    min_personas: int = 3
    max_personas: int = 6
    summary_cadence_ticks: int = 7


class NetworkSimulatorRequest(BaseModel):
    """Request model for network simulation execution."""

    query: str
    max_ticks: int = 16
    seed: Optional[int] = None
    min_nodes: int = 15
    max_nodes: int = 30
    scenario_id: str = "business_network_v1"
    allow_internet: bool = True
    data_context_path: Optional[str] = None


class NetworkShockRequest(BaseModel):
    """Request model for shock injection into an active network session."""

    shock_type: str
    summary: str
    severity: float
    targets: list[str] = Field(default_factory=list)


class ObserverChatRequest(BaseModel):
    """Request model for post-run observer chat."""

    question: str


def _ensure_simulator_import_path() -> None:
    simulator_root = Path(__file__).resolve().parent / "simulator_agent"
    simulator_root_str = str(simulator_root)
    if simulator_root_str not in sys.path:
        sys.path.insert(0, simulator_root_str)


def _get_simulator_agent():
    _ensure_simulator_import_path()
    from simulator_agent.src import agent as simulator_agent

    return simulator_agent


def _ensure_deep_simulator_import_path() -> None:
    backend_root = Path(__file__).resolve().parent
    backend_root_str = str(backend_root)
    if backend_root_str not in sys.path:
        sys.path.insert(0, backend_root_str)


def _get_deep_simulator_agent():
    _ensure_deep_simulator_import_path()
    from deep_simulation_agent.src import agent as deep_simulator_agent

    return deep_simulator_agent


def _ensure_network_simulator_import_path() -> None:
    backend_root = Path(__file__).resolve().parent
    backend_root_str = str(backend_root)
    if backend_root_str not in sys.path:
        sys.path.insert(0, backend_root_str)


def _get_network_simulator_agent():
    _ensure_network_simulator_import_path()
    from network_simulation_agent.src import agent as network_simulator_agent

    return network_simulator_agent


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


def _build_deep_simulator_initial_state(request: DeepSimulatorRequest) -> dict[str, Any]:
    return {
        "query": request.query,
        "max_ticks": request.max_ticks,
        "seed": request.seed,
        "scenario_id": request.scenario_id,
        "min_personas": request.min_personas,
        "max_personas": request.max_personas,
        "summary_cadence_ticks": request.summary_cadence_ticks,
    }


def _build_network_simulator_initial_state(request: NetworkSimulatorRequest) -> dict[str, Any]:
    return {
        "query": request.query,
        "max_ticks": request.max_ticks,
        "seed": request.seed,
        "min_nodes": request.min_nodes,
        "max_nodes": request.max_nodes,
        "scenario_id": request.scenario_id,
        "allow_internet": request.allow_internet,
        "data_context_path": request.data_context_path,
    }


def _ndjson_line(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=str) + "\n"


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
        supabase.table('department').select('count').execute()
        
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
                stream_mode=["updates", "values", "custom"],
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
                elif part_type == "values":
                    values = part.get("data")
                    if isinstance(values, dict):
                        latest_values = values
                elif part_type == "custom":
                    custom_data = part.get("data")
                    if isinstance(custom_data, dict):
                        yield _ndjson_line(
                            {
                                "type": "custom",
                                "event": custom_data.get("event"),
                                "data": _safe_json_payload(custom_data),
                            }
                        )

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


@app.post("/api/deep-simulator/run")
async def run_deep_simulator(request: DeepSimulatorRequest):
    """
    Execute deep 2D simulator and return final result in one response.
    """
    try:
        deep_simulator_agent = _get_deep_simulator_agent()
        initial_state = _build_deep_simulator_initial_state(request)
        result = await asyncio.to_thread(deep_simulator_agent.invoke, initial_state)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deep simulator run failed: {str(e)}")


@app.post("/api/deep-simulator/stream")
async def stream_deep_simulator(request: DeepSimulatorRequest):
    """
    Stream deep simulator world updates and subagent chunks as NDJSON.
    """
    deep_simulator_agent = _get_deep_simulator_agent()
    initial_state = _build_deep_simulator_initial_state(request)

    async def event_stream():
        try:
            async for event in deep_simulator_agent.astream(initial_state):
                yield _ndjson_line(_safe_json_payload(event))
        except Exception as e:
            yield _ndjson_line({"type": "error", "error": str(e)})
            yield _ndjson_line({"type": "done"})

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/api/network-simulator/run")
async def run_network_simulator(request: NetworkSimulatorRequest):
    """
    Execute network simulation and return final response in one payload.
    """
    try:
        network_simulator_agent = _get_network_simulator_agent()
        initial_state = _build_network_simulator_initial_state(request)
        result = await asyncio.to_thread(network_simulator_agent.invoke, initial_state)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Network simulator run failed: {str(e)}")


@app.post("/api/network-simulator/stream")
async def stream_network_simulator(request: NetworkSimulatorRequest):
    """
    Stream network simulation events as NDJSON.
    """
    network_simulator_agent = _get_network_simulator_agent()
    initial_state = _build_network_simulator_initial_state(request)

    async def event_stream():
        try:
            async for event in network_simulator_agent.astream(initial_state):
                yield _ndjson_line(_safe_json_payload(event))
        except Exception as e:
            yield _ndjson_line({"type": "error", "error": str(e)})
            yield _ndjson_line({"type": "done"})

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/api/network-simulator/{session_id}/shock")
async def add_network_simulator_shock(session_id: str, request: NetworkShockRequest):
    """
    Queue shock event for the next stream tick of the given session.
    """
    try:
        _ensure_network_simulator_import_path()
        from network_simulation_agent.src.engine import SESSION_STORE
        from network_simulation_agent.src.schema import ShockEvent

        shock = ShockEvent(
            shock_type=request.shock_type,
            summary=request.summary,
            severity=request.severity,
            targets=request.targets,
        )
        SESSION_STORE.queue_shock(session_id, shock)
        return {"status": "ok", "session_id": session_id, "queued_shock": shock.model_dump(mode="json")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue shock: {str(e)}")


@app.post("/api/network-simulator/{session_id}/observer-chat")
async def network_simulator_observer_chat(session_id: str, request: ObserverChatRequest):
    """
    Return observer answer grounded to persisted session artifacts.
    """
    try:
        _ensure_network_simulator_import_path()
        from network_simulation_agent.src.engine import SESSION_STORE
        from network_simulation_agent.src.observer import build_observer_answer

        summary = SESSION_STORE.get_observer_report(session_id)
        backend_root = Path(__file__).resolve().parent
        base_dir = backend_root / "network_simulation_agent"
        response = build_observer_answer(
            base_dir=base_dir,
            session_id=session_id,
            question=request.question,
            summary=summary or "",
        )
        return {"status": "ok", "session_id": session_id, **response}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Observer chat failed: {str(e)}")


@app.get("/api/network-simulator/{session_id}/storyline")
async def download_network_simulator_storyline(session_id: str):
    """
    Download final storyline markdown artifact for a completed network simulation session.
    """
    try:
        _ensure_network_simulator_import_path()
        from network_simulation_agent.src.observer import storyline_path

        backend_root = Path(__file__).resolve().parent
        base_dir = backend_root / "network_simulation_agent"
        target = storyline_path(base_dir=base_dir, session_id=session_id)
        if not target.exists():
            raise HTTPException(status_code=404, detail="Storyline artifact not found for this session.")
        return FileResponse(
            path=target,
            filename=f"{session_id}_storyline.md",
            media_type="text/markdown; charset=utf-8",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storyline download failed: {str(e)}")


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    submitted_by: str = Form("system")
):
    """Upload a document, store metadata, and trigger ingestion."""
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md']
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {ext} not supported. Allowed: {', '.join(allowed_extensions)}"
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            temp_path = tmp_file.name

        try:
            from services.cloudinary_service import get_cloudinary_service
            from services.document_service import DocumentIngestor
            from services.data_writer_agent import get_data_writer_agent

            cloudinary_service = get_cloudinary_service()
            upload_result = cloudinary_service.upload_document(temp_path, file.filename)
            cloudinary_url = upload_result["url"]

            db_result = db.client.table("source_document").insert({
                "file_path": cloudinary_url,
                "doc_type": doc_type,
                "submitted_by": submitted_by,
                "submitted_at": datetime.now().isoformat(),
            }).execute()
            source_id = db_result.data[0]["source_id"]

            ingestor = DocumentIngestor()
            extracted_records = ingestor.ingest_document(temp_path, doc_type, source_id)

            if extracted_records:
                data_writer = get_data_writer_agent(db.client)
                write_results = await data_writer.write_records(extracted_records, source_id)
            else:
                write_results = {"message": "No records extracted from document"}

            return {
                "success": True,
                "source_id": source_id,
                "document_url": cloudinary_url,
                "filename": file.filename,
                "doc_type": doc_type,
                "records_extracted": len(extracted_records) if extracted_records else 0,
                "write_results": write_results
            }
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload process failed: {str(e)}")


@app.get("/api/documents")
async def list_documents(doc_type: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List uploaded documents with optional type filter and pagination."""
    try:
        query = db.client.table("source_document").select("*").order("created_at", desc=True)
        if doc_type:
            query = query.eq("doc_type", doc_type)
        result = query.range(offset, offset + limit - 1).execute()
        return {"documents": result.data, "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/api/documents/{source_id}")
async def get_document(source_id: int):
    """Get single document by source_id."""
    try:
        result = db.client.table("source_document").select("*").eq("source_id", source_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"document": result.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.delete("/api/documents/{source_id}")
async def delete_document(source_id: int):
    """Delete a document record by source_id."""
    try:
        db.client.table("source_document").delete().eq("source_id", source_id).execute()
        return {"success": True, "message": f"Document {source_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


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
