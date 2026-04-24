"""
Shared Zhipu AI LLM client and JSON utilities for domain agents.
Mirrors the hrlegal branch helper so HR, Legal, and Finance agents
can call llm_json() with their own rich system prompts.
"""
import json
import re
from functools import lru_cache
from openai import AsyncOpenAI
from config import get_settings


@lru_cache()
def get_llm_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.zhipu_api_key or "sk-placeholder",
        base_url=settings.zhipu_base_url,
    )


def get_model() -> str:
    return get_settings().zhipu_model


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return json.loads(match.group(1))

    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"Cannot extract JSON from LLM response: {text[:300]}")


async def llm_json(system: str, user: str, temperature: float = 0.2, max_tokens: int = 800) -> dict:
    """Call Zhipu AI and return parsed JSON dict. Raises on empty/failed response."""
    client = get_llm_client()
    model = get_model()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    raw = (response.choices[0].message.content or "").strip()
    if not raw:
        raise ValueError("LLM returned empty content")
    return extract_json(raw)


async def llm_text(system: str, user: str, temperature: float = 0.3, max_tokens: int = 300) -> str:
    """Call Zhipu AI and return plain text. Raises on empty response."""
    client = get_llm_client()
    model = get_model()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise ValueError("LLM returned empty content")
    return text
