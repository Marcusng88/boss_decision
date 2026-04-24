from __future__ import annotations

import json
import os
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _extract_json_object_text(raw: str) -> str:
    raw = _strip_json_fence(raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return raw[start : end + 1]
    return ""


@dataclass
class LLMResponse:
    text: str
    model: str


class UnifiedLLMClient:
    """
    Clean client optimized for Gemini-2.5-flash-lite.
    """

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")  # IMPORTANT: normalize once

    @classmethod
    def from_settings(cls) -> Optional["UnifiedLLMClient"]:
        """
        Enforces correct pairing of API key + endpoint for Gemini.
        """
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()

        if provider == "gemini":
            return cls(
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=os.getenv("LLM_MODEL", "gemini-2.5-flash-lite"),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            )

        return None

    def _endpoint(self) -> str:
        """
        No guessing. Always correct endpoint.
        """
        return self.base_url

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _extract_text(self, data: Dict[str, Any]) -> str:
        """
        Handles multiple response formats safely.
        """
        try:
            # Standard OpenAI format
            return data["choices"][0]["message"]["content"]
        except Exception:
            # fallback: print debug-friendly info
            return json.dumps(data)[:500]

    async def acomplete_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 600,
    ) -> LLMResponse:

        url = self._endpoint()
        headers = self._headers()
        payload = self._payload(system_prompt, user_prompt, temperature, max_tokens)

        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(3):
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    
                    if resp.status_code == 429:
                        wait_time = (attempt + 1) * 2
                        print(f"[LLM] Rate limited (429). Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    resp.raise_for_status()
                    data = resp.json()
                    text = self._extract_text(data)
                    return LLMResponse(text=text, model=self.model)

                except Exception as e:
                    if attempt == 2:
                        raise Exception(f"LLM request failed after 3 attempts: {url} | {str(e)}")
                    await asyncio.sleep(1)
        
        raise Exception("LLM request failed due to unknown error.")

    def complete_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 600,
    ) -> LLMResponse:

        url = self._endpoint()
        headers = self._headers()
        payload = self._payload(system_prompt, user_prompt, temperature, max_tokens)

        with httpx.Client(timeout=60.0) as client:
            try:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()

                data = resp.json()
                text = self._extract_text(data)

                return LLMResponse(text=text, model=self.model)

            except Exception as e:
                raise Exception(f"LLM request failed: {url} | {str(e)}")

    async def acomplete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 600,
    ) -> Tuple[Dict[str, Any], str]:

        for attempt in range(2):
            prompt = user_prompt
            if attempt == 1:
                prompt += "\n\nReturn ONLY valid JSON."

            response = await self.acomplete_text(
                system_prompt, prompt, temperature, max_tokens
            )

            json_text = _extract_json_object_text(response.text)

            if not json_text:
                if attempt == 0:
                    continue
                raise Exception("Invalid JSON response")

            try:
                return json.loads(json_text), response.model
            except json.JSONDecodeError:
                if attempt == 0:
                    continue
                raise Exception("JSON parsing failed")

        raise Exception("JSON extraction failed")

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 600,
    ) -> Tuple[Dict[str, Any], str]:

        for attempt in range(2):
            prompt = user_prompt
            if attempt == 1:
                prompt += "\n\nReturn ONLY valid JSON."

            response = self.complete_text(
                system_prompt, prompt, temperature, max_tokens
            )

            json_text = _extract_json_object_text(response.text)

            if not json_text:
                if attempt == 0:
                    continue
                raise Exception("Invalid JSON response")

            try:
                return json.loads(json_text), response.model
            except json.JSONDecodeError:
                if attempt == 0:
                    continue
                raise Exception("JSON parsing failed")

        raise Exception("JSON extraction failed")