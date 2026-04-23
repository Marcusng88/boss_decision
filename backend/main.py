"""
Main FastAPI application for AI Boss Decision Engine.
Multi-agent decision support system with LangChain integration.
"""
from pathlib import Path
import tempfile

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from config import get_settings
from services.local_knowledge_service import LocalKnowledgeService
from services.document_service import DocumentIngestor
from services.llm_client import UnifiedLLMClient
from agents import (
    HRAgent,
    SalesAgent,
    LegalAgent,
    MarketingAgent,
    SupplyChainAgent,
    ManagerAgent,
)

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

# Initialize local knowledge service and agents
knowledge = LocalKnowledgeService()
hr_agent = HRAgent(knowledge)
sales_agent = SalesAgent(knowledge)
legal_agent = LegalAgent(knowledge)
marketing_agent = MarketingAgent(knowledge)
supply_chain_agent = SupplyChainAgent(knowledge)
manager_agent = ManagerAgent([
    hr_agent,
    sales_agent,
    legal_agent,
    marketing_agent,
    supply_chain_agent,
])
document_ingestor = DocumentIngestor()


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
    document_summary: Optional[str] = None
    document_department: Optional[str] = None
    document_entities: Optional[list[dict]] = None
    document_tags: Optional[list[str]] = None


class EmployeeResponse(BaseModel):
    """Response model for employee endpoint."""
    employee: dict
    hr_records: list[dict]
    sales_records: list[dict]


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
    """Detailed health check with local knowledge workspace readiness."""
    try:
        required_dirs = [
            knowledge.workplaces_root,
            knowledge.documents_dir,
            knowledge.raw_dir,
            knowledge.entities_dir,
            knowledge.relationship_dir,
        ]

        missing = [str(path) for path in required_dirs if not path.exists()]
        if missing:
            raise RuntimeError(f"Missing required directories: {missing}")

        return {
            "status": "healthy",
            "storage": "local_filesystem",
            "workplaces_root": str(knowledge.workplaces_root)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/api/health/llm")
async def llm_health_check():
    """Check LLM connectivity and model availability without exposing secrets."""
    client = UnifiedLLMClient.from_settings()
    if client is None:
        raise HTTPException(status_code=503, detail="LLM not configured (missing API key)")

    try:
        response = client.complete_text(
            system_prompt="You are a health-check assistant.",
            user_prompt="Reply with exactly: ok",
            temperature=0.0,
            max_tokens=12,
        )
        return {
            "status": "healthy",
            "llm_model": client.model,
            "llm_response": (response.text or "")[:40],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "llm_model": client.model,
                "llm_endpoint_candidates": client.endpoint_candidates,
                "error": str(exc),
            },
        )


@app.get("/api/employees/{employee_id}")
async def get_employee(employee_id: int):
    """Get employee profile with related records."""
    try:
        employee = await knowledge.get_employee(employee_id)
        hr_records = await knowledge.get_employee_hr_records(employee_id)
        sales_records = await knowledge.get_employee_sales_records(employee_id)
        
        return {
            "employee": employee,
            "hr_records": hr_records,
            "sales_records": sales_records
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Employee not found: {str(e)}")


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """Get decision case with evidence and output."""
    try:
        evidence = await knowledge.get_case_evidence(case_id)
        decision = await knowledge.get_decision_output(case_id)
        
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
    
    Runs local multi-agent orchestration using file-based knowledge.
    """
    try:
        return await _run_analysis(
            query=request.query,
            context=request.context,
            target_type=request.target_type,
            target_id=request.target_id,
            submitted_by=request.submitted_by,
            document_analysis={
                "summary": request.document_summary,
                "department": request.document_department,
                "entities": request.document_entities or [],
                "tags": request.document_tags or [],
            } if request.document_summary or request.document_department else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/analyze/upload")
async def analyze_query_with_upload(
    query: str = Form(...),
    context: str | None = Form(default=None),
    target_type: str | None = Form(default=None),
    target_id: int | None = Form(default=None),
    submitted_by: str | None = Form(default="frontend"),
    document: UploadFile | None = File(default=None),
):
    """Analyze decision query with optional uploaded file context."""
    try:
        extracted_document = None

        if document is not None:
            suffix = Path(document.filename or "upload.bin").suffix or ".bin"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                data = await document.read()
                tmp.write(data)
                tmp_path = tmp.name

            try:
                extracted_document = await document_ingestor.aprocess(tmp_path)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        response = await _run_analysis(
            query=query,
            context=context,
            target_type=target_type,
            target_id=target_id,
            submitted_by=submitted_by,
            document_analysis=extracted_document,
        )

        if extracted_document:
            response["document_analysis"] = extracted_document
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload analysis failed: {str(e)}")


async def _run_analysis(
    *,
    query: str,
    context: str | None,
    target_type: str | None,
    target_id: int | None,
    submitted_by: str | None,
    document_analysis: dict | None,
):
    case = await knowledge.create_decision_case(
        question=query,
        context=context,
        target_type=target_type,
        target_id=target_id,
        submitted_by=submitted_by,
    )

    orchestration_context = {
        "target_type": target_type,
        "target_id": target_id,
        "context": context,
        "submitted_by": submitted_by,
        "force_simple_llm_subagents": False,
        "knowledge_paths": {
            "entities": str(knowledge.entities_dir),
            "relationships": str(knowledge.relationship_dir),
            "raw": str(knowledge.raw_dir),
        },
    }

    if document_analysis:
        orchestration_context["document_summary"] = document_analysis.get("summary")
        orchestration_context["document_department"] = document_analysis.get("department")
        orchestration_context["document_entities"] = document_analysis.get("entities", [])
        orchestration_context["document_tags"] = document_analysis.get("tags", [])
        orchestration_context["document_metadata"] = document_analysis.get("metadata", {})

    orchestration = await manager_agent.orchestrate_dynamic(
        query=query,
        context=orchestration_context,
    )
    final_decision = orchestration["final_decision"]

    for insight in orchestration.get("agent_insights", []):
        for evidence in insight.get("evidence_used", []):
            record_id = evidence.get("record_id") or evidence.get("path") or "unknown"
            source_table = evidence.get("source") or "local_knowledge"
            await knowledge.save_case_evidence(
                case_id=case["case_id"],
                source_table=str(source_table),
                record_id=str(record_id),
                relevance_score=0.8,
                retrieval_method="filesystem",
                notes=evidence.get("type") or insight.get("agent_name"),
            )

    await knowledge.save_decision_output(
        case_id=case["case_id"],
        recommendation=final_decision["recommendation"],
        risk_level=final_decision["risk_level"],
        confidence_score=final_decision["confidence_score"],
        rationale=final_decision["rationale"],
        conservative_view=orchestration.get("conservative_view"),
        aggressive_view=orchestration.get("aggressive_view"),
        manager_persona=final_decision.get("manager_persona", "balanced"),
    )

    return {
        "status": "completed",
        "case_id": case["case_id"],
        "query": query,
        "routing": orchestration.get("routing", {}),
        "final_decision": final_decision,
        "agent_insights": orchestration.get("agent_insights", []),
        "conservative_view": orchestration.get("conservative_view", ""),
        "aggressive_view": orchestration.get("aggressive_view", ""),
    }


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
