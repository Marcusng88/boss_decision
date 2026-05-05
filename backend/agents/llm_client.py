"""
Shared Zhipu AI (OpenAI-compatible) LLM client and JSON utilities.
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


async def llm_json(system: str, user: str, temperature: float = 0.2) -> dict:
    """Call the LLM and return parsed JSON dict."""
    client = get_llm_client()
    model = get_model()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    raw = response.choices[0].message.content or ""
    return extract_json(raw)
