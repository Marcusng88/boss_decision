"""
Main FastAPI application for AI Boss Decision Engine.
Multi-agent decision support system with LLM integration.
"""
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from config import get_settings
from db import DatabaseService
from agents import ManagerAgent, detect_intent
from agents.base_agent import AgentInsight

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
    selected_agents: Optional[List[str]] = None   # user-chosen agents override auto-detect


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
    """Standard (non-streaming) decision endpoint."""
    try:
        intent = await detect_intent(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent detection failed: {str(e)}")

    if request.selected_agents:
        intent["agents"] = request.selected_agents

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
        pass

    try:
        result = await manager.orchestrate(request.query, intent)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent pipeline failed: {str(e)}")

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


@app.post("/api/analyze/stream")
async def analyze_stream(request: AnalyzeRequest):
    """SSE streaming endpoint — inline generator, asyncio.wait(FIRST_COMPLETED) for parallelism.

    No timeouts on individual LLM calls — the LLM API is slow and timeouts cause
    CancelledError (a BaseException) to bypass except-Exception handlers, corrupting
    the intent/context and silently dropping agents.  The streaming display provides
    progress feedback so the user sees activity while waiting.
    """

    def sse(event: Dict[str, Any]) -> str:
        return f"data: {json.dumps(event)}\n\n"

    async def event_stream():
        try:
            yield sse({"type": "status", "message": "Detecting intent…"})

            # 1. Intent detection — no timeout; detect_intent() has its own LLM fallback
            try:
                intent = await detect_intent(request.query)
            except Exception:
                # Should never reach here since detect_intent() catches internally,
                # but keep as a last-resort safety net using keyword fallback.
                from agents.intent_detector import _fallback_detect
                intent = _fallback_detect(request.query)

            if request.selected_agents:
                intent["agents"] = request.selected_agents

            agent_names: List[str] = intent.get("agents", [])
            yield sse({"type": "intent", "agents": agent_names})

            # 2. Launch all agent tasks in parallel — NO per-agent timeouts.
            #    Slow LLM calls just take time; don't kill them silently.
            valid_names = [n for n in agent_names if n in manager._agent_registry]

            for name in valid_names:
                yield sse({"type": "agent_start", "agent": name})

            task_to_name: Dict[asyncio.Task, str] = {
                asyncio.ensure_future(
                    manager._agent_registry[name].run(request.query, intent)
                ): name
                for name in valid_names
            }

            agent_insights: List[AgentInsight] = []
            pending = set(task_to_name.keys())

            # Stream each result as it completes
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    name = task_to_name[task]
                    try:
                        insight = task.result()
                        if isinstance(insight, AgentInsight):
                            agent_insights.append(insight)
                            yield sse({"type": "agent_done", "agent": name,
                                       "insight": insight.model_dump()})
                    except Exception:
                        pass  # agent raised — skip but don't abort the stream

            # 3. Synthesis — no timeout; let the LLM respond naturally
            yield sse({"type": "status", "message": "Synthesizing perspectives…"})

            try:
                if agent_insights:
                    synthesis = await manager._synthesize_with_llm(agent_insights, request.query)
                    conservative = synthesis.get("conservative", {})
                    aggressive = synthesis.get("aggressive", {})
                    final_decision = synthesis.get("final_decision", {})
                else:
                    empty = manager._empty_result(request.query)
                    conservative = empty["conservative_view"]
                    aggressive = empty["aggressive_view"]
                    final_decision = empty["final_decision"]
            except Exception:
                fallback = (
                    manager._rule_based_synthesis(agent_insights)
                    if agent_insights else manager._empty_result(request.query)
                )
                conservative = fallback.get("conservative", fallback.get("conservative_view", {}))
                aggressive = fallback.get("aggressive", fallback.get("aggressive_view", {}))
                final_decision = fallback.get("final_decision", {})

            yield sse({"type": "synthesis",
                       "conservative": conservative, "aggressive": aggressive})

            full_result = {
                "case_id": None,
                "query": request.query,
                "agents_invoked": agent_names,
                "agent_insights": [i.model_dump() for i in agent_insights],
                "conservative_view": conservative,
                "aggressive_view": aggressive,
                "final_decision": final_decision,
            }
            yield sse({"type": "complete", "result": full_result})

        except asyncio.CancelledError:
            return  # client disconnected — exit cleanly
        except Exception as e:
            yield sse({"type": "error", "message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )
