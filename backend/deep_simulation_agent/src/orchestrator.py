from __future__ import annotations

import json
import logging
import os
import random
from pathlib import Path
from typing import Any
from typing import AsyncIterator

from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

from .personas import propose_personas
from .rules import parse_action_intent
from .schema import ActionIntent
from .schema import AgentObservation
from .schema import PersonaProfile

logger = logging.getLogger(__name__)

_MARKDOWN_SYSTEM_APPENDIX = """
Markdown behavior contract:
- Use `## Situation`, `## Evidence`, `## Analysis`, `## Recommendation`, `## Validation`.
- Keep bullets flat and concrete.
- Use inline code for metrics and literals like `revenue`, `+10%`.
- Use LaTeX for math when helpful, for example `$Revenue = Price \\times Volume$`.
- Do not emit raw JSON in final prose.
- If the world state should change, call `submit_action_intent`.
"""


def _load_env() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    load_dotenv(backend_root / ".env", override=False)
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = google_key


def _infer_model_name() -> str:
    _load_env()
    if os.getenv("SIMULATOR_MODEL"):
        return str(os.getenv("SIMULATOR_MODEL"))
    if os.getenv("OPENAI_API_KEY"):
        name = os.getenv("LLM_MODEL", "gpt-4.1-mini")
        return name if ":" in name else f"openai:{name}"
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return "google_genai:gemini-3.1-flash-lite-preview"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic:claude-3-5-sonnet-latest"
    return "openai:gpt-4.1-mini"


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        return "".join(chunks)
    return str(content) if content is not None else ""


def _extract_tool_call_chunks(message_chunk: Any) -> list[dict[str, Any]]:
    chunks = getattr(message_chunk, "tool_call_chunks", None)
    if isinstance(chunks, list):
        return [chunk for chunk in chunks if isinstance(chunk, dict)]
    content = getattr(message_chunk, "content", None)
    if isinstance(content, list):
        return [item for item in content if isinstance(item, dict) and str(item.get("type")) == "tool_call_chunk"]
    return []


class DeepOrchestrator:
    def __init__(
        self,
        query: str,
        scenario: dict[str, Any],
        min_personas: int,
        max_personas: int,
        rng: random.Random,
        docs_root: Path,
    ):
        _load_env()
        self.query = query
        self.scenario = scenario
        self.min_personas = min_personas
        self.max_personas = max_personas
        self.rng = rng
        self.docs_root = docs_root
        self.model_name = _infer_model_name()
        self.selector_model = self._init_chat_model(self.model_name, 0.2)
        self.parser_model = self._init_chat_model(self.model_name, 0.0)
        self.observer_model = self._init_chat_model(self.model_name, 0.2)
        self._persona_agents: dict[str, Any] = {}
        self._active_intent_sinks: dict[str, list[ActionIntent]] = {}
        self._force_fallback_personas: set[str] = set()
        self.personas = propose_personas(
            query=query,
            scenario=scenario,
            min_personas=min_personas,
            max_personas=max_personas,
            rng=rng,
            selector_model=self.selector_model,
            base_docs_dir=docs_root,
        )
        shared_paths = [str(item) for item in scenario.get("shared_allowlist", []) if isinstance(item, str)]
        if shared_paths:
            shared_roots = []
            for rel in shared_paths:
                root = (docs_root / rel).resolve()
                if root.exists() and root.is_dir():
                    shared_roots.append(str(root))
            if shared_roots:
                for persona in self.personas:
                    merged = set(persona.allowed_paths)
                    merged.update(shared_roots)
                    persona.allowed_paths = sorted(merged)

    def _init_chat_model(self, model_name: str, temperature: float) -> Any | None:
        try:
            from langchain.chat_models import init_chat_model

            return init_chat_model(model=model_name, temperature=temperature)
        except Exception as exc:
            logger.warning("deep.orchestrator.model_init_failed model=%s error=%s", model_name, exc)
            return None

    def _build_tools(self, persona: PersonaProfile) -> list[Any]:
        allowed_roots = [Path(root).resolve() for root in persona.allowed_paths]
        persona_id = persona.id

        @tool("read_allowed_file")
        def read_allowed_file(path: str, max_chars: int = 2400) -> str:
            """Read textual files from the persona allowlist roots only."""
            target = Path(path).resolve()
            if not any(str(target).startswith(str(root)) for root in allowed_roots):
                return f"Denied: path `{target}` is outside allowed roots."
            if not target.exists() or not target.is_file():
                return f"File not found: `{target}`."
            try:
                text = target.read_text(encoding="utf-8", errors="ignore")
                return text[: max(200, min(max_chars, 12000))]
            except Exception as exc:
                return f"Read failed: {exc}"

        @tool("internet_search")
        def internet_search(query: str, max_results: int = 3) -> str:
            """Search current web context using Tavily."""
            api_key = os.getenv("TAVILY_API_KEY", "").strip()
            if not api_key:
                return "TAVILY_API_KEY missing."
            try:
                client = TavilyClient(api_key=api_key)
                result = client.search(query=query, max_results=max(1, min(max_results, 6)))
                rows: list[str] = []
                for item in result.get("results", [])[:6]:
                    title = str(item.get("title", "")).strip()
                    url = str(item.get("url", "")).strip()
                    snippet = str(item.get("content", "")).replace("\n", " ").strip()
                    rows.append(f"- {title} ({url}): {snippet[:180]}")
                return "\n".join(rows) if rows else "No search results."
            except Exception as exc:
                return f"Search failed: {exc}"

        @tool("submit_action_intent")
        def submit_action_intent(
            action_type: str,
            args_json: str = "{}",
            confidence: float = 0.6,
            rationale_md: str = "",
        ) -> str:
            """Submit a structured action intent for world-state updates."""
            sink = self._active_intent_sinks.setdefault(persona_id, [])
            try:
                args = json.loads(args_json) if args_json.strip() else {}
                if not isinstance(args, dict):
                    args = {}
            except Exception:
                args = {}
            intent = ActionIntent(
                persona_id=persona_id,
                tick=0,
                action_type=action_type,  # type: ignore[arg-type]
                args=args,
                confidence=max(0.0, min(1.0, float(confidence))),
                rationale_md=rationale_md[:1200],
                requested_via_tool=True,
            )
            sink.append(intent)
            return f"intent accepted for {persona_id}: {action_type}"

        return [internet_search, read_allowed_file, submit_action_intent]

    def _get_persona_agent(self, persona: PersonaProfile) -> Any:
        if persona.id in self._force_fallback_personas:
            return _FallbackPersonaAgent(persona=persona)
        cached = self._persona_agents.get(persona.id)
        if cached is not None:
            return cached
        system_prompt = f"{persona.system_prompt.strip()}\n\n{_MARKDOWN_SYSTEM_APPENDIX.strip()}"
        tools = self._build_tools(persona)
        try:
            from deepagents import create_deep_agent

            model = self._init_chat_model(self.model_name, 0.2)
            if model is not None:
                agent = create_deep_agent(model=model, system_prompt=system_prompt, tools=tools)
            else:
                agent = create_deep_agent(model=self.model_name, system_prompt=system_prompt, tools=tools)
        except Exception as exc:
            logger.warning("deep.orchestrator.agent_create_failed persona=%s error=%s", persona.id, exc)
            agent = _FallbackPersonaAgent(persona=persona)
        self._persona_agents[persona.id] = agent
        return agent

    def select_active_personas_for_tick(self, tick: int, churn_risk: float) -> list[PersonaProfile]:
        if tick <= 2:
            return self.personas[:]
        desired = 2
        if churn_risk >= 5.0:
            desired = 3
        desired = min(desired, len(self.personas))
        pool = self.personas[:]
        selected: list[PersonaProfile] = []
        for _ in range(desired):
            if not pool:
                break
            total = sum(max(0.1, item.weight) for item in pool)
            cursor = self.rng.random() * total
            running = 0.0
            chosen = pool[0]
            for candidate in pool:
                running += max(0.1, candidate.weight)
                if running >= cursor:
                    chosen = candidate
                    break
            selected.append(chosen)
            pool.remove(chosen)
        selected.sort(key=lambda persona: persona.id)
        return selected

    async def stream_persona(
        self,
        persona: PersonaProfile,
        observation: AgentObservation,
    ) -> AsyncIterator[dict[str, Any]]:
        agent = self._get_persona_agent(persona)
        sink: list[ActionIntent] = []
        self._active_intent_sinks[persona.id] = sink
        prompt = (
            "React to this simulation observation. "
            "Stream your analysis in markdown. "
            "Use tools when needed. "
            "Only call `submit_action_intent` when you are proposing a concrete world action. "
            f"Observation: {json.dumps(observation.model_dump())}"
        )
        collected = ""
        latest_values: dict[str, Any] | None = None
        seen_tool_keys: set[str] = set()
        try:
            async for part in agent.astream(
                {"messages": [{"role": "user", "content": prompt}]},
                stream_mode=["messages", "values"],
                version="v2",
            ):
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "messages":
                    data = part.get("data")
                    if not isinstance(data, (tuple, list)) or not data:
                        continue
                    message_chunk = data[0]
                    text = _extract_text_content(getattr(message_chunk, "content", ""))
                    if text:
                        collected += text
                        yield {"type": "agent_chunk", "persona_id": persona.id, "chunk": text}
                    for tool_chunk in _extract_tool_call_chunks(message_chunk):
                        tool_name = str(tool_chunk.get("name") or tool_chunk.get("tool_name") or "").strip()
                        tool_id = str(tool_chunk.get("id") or "").strip()
                        if not tool_name:
                            continue
                        key = f"{tool_id}:{tool_name}" if tool_id else tool_name
                        if key in seen_tool_keys:
                            continue
                        seen_tool_keys.add(key)
                        yield {"type": "agent_tool_call", "persona_id": persona.id, "tool_call": f"{tool_name}(...)"}
                elif part.get("type") == "values":
                    values = part.get("data")
                    if isinstance(values, dict):
                        latest_values = values
        except Exception as exc:
            logger.warning("deep.orchestrator.persona_stream_failed persona=%s error=%s", persona.id, exc)
            self._force_fallback_personas.add(persona.id)
            self._persona_agents[persona.id] = _FallbackPersonaAgent(persona=persona)

        if not collected and latest_values:
            messages = latest_values.get("messages")
            if isinstance(messages, list):
                for item in reversed(messages):
                    content = getattr(item, "content", item.get("content") if isinstance(item, dict) else "")
                    extracted = _extract_text_content(content)
                    if extracted.strip():
                        collected = extracted
                        break
        if not collected:
            collected = (
                "## Situation\n"
                f"{persona.name} moved to deterministic fallback for this run.\n\n"
                "## Evidence\n"
                "- External model stream unavailable.\n\n"
                "## Analysis\n"
                "Applying conservative posture with bounded downside.\n\n"
                "## Recommendation\n"
                "Run phased test before global rollout.\n\n"
                "## Validation\n"
                "Track 7-day conversion and churn deltas."
            )

        selected_intent: ActionIntent | None = None
        for intent in sink:
            intent.tick = observation.tick
            if selected_intent is None or intent.confidence > selected_intent.confidence:
                selected_intent = intent
        if selected_intent is None:
            parsed = parse_action_intent(
                persona=persona,
                tick=observation.tick,
                transcript_md=collected,
                parser_model=self.parser_model,
            )
            selected_intent = parsed
        yield {
            "type": "persona_complete",
            "persona_id": persona.id,
            "transcript": collected,
            "intent": selected_intent.model_dump() if selected_intent is not None else None,
        }
        self._active_intent_sinks.pop(persona.id, None)


class _FallbackPersonaAgent:
    def __init__(self, persona: PersonaProfile):
        self.persona = persona

    async def astream(self, *_args: Any, **_kwargs: Any) -> AsyncIterator[dict[str, Any]]:
        text = (
            "## Situation\n"
            f"Acting as {self.persona.name}, model fallback mode is active.\n\n"
            "## Evidence\n"
            "- External model unavailable, using deterministic local response.\n\n"
            "## Analysis\n"
            "Maintain conservative posture and avoid irreversible moves.\n\n"
            "## Recommendation\n"
            "Run small controlled experiment and collect elasticity signals.\n\n"
            "## Validation\n"
            "Track churn and conversion over the next 7 days."
        )
        chunk_size = 48
        for start in range(0, len(text), chunk_size):
            chunk = text[start : start + chunk_size]
            fake_chunk = type("Chunk", (), {"content": chunk})()
            yield {"type": "messages", "data": (fake_chunk, {"langgraph_node": "fallback"})}
        yield {"type": "values", "data": {"messages": [{"content": text}]}}
