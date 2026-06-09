import asyncio
import os
import json
import re
import time
from groq import Groq, AsyncGroq
from groq import APIConnectionError, RateLimitError
from dotenv import load_dotenv

load_dotenv()

MODEL_FAST = "llama-3.1-8b-instant"     # guardrail + compression — speed matters
MODEL_BEST = "llama-3.3-70b-versatile"  # all content agents — quality matters

_RETRY_DELAYS = [8, 20, 45]


def _new_client() -> Groq:
    return Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0, timeout=120.0)


def _new_async_client() -> AsyncGroq:
    return AsyncGroq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0, timeout=120.0)


# ── Synchronous (used by Streamlit) ───────────────────────────────────────────

def call_claude(prompt: str, system: str, max_tokens: int = 2048,
                model: str = MODEL_BEST) -> str:
    last_exc: Exception | None = None
    for delay in [0] + _RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            client = _new_client()
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except (APIConnectionError, RateLimitError) as exc:
            last_exc = exc
    raise last_exc  # type: ignore[misc]


# ── Asynchronous (used by FastAPI + parallel LangGraph nodes) ─────────────────

async def acall_claude(prompt: str, system: str, max_tokens: int = 2048,
                       model: str = MODEL_BEST) -> str:
    last_exc: Exception | None = None
    for delay in [0] + _RETRY_DELAYS:
        if delay:
            await asyncio.sleep(delay)
        try:
            client = _new_async_client()
            response = await client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except (APIConnectionError, RateLimitError) as exc:
            last_exc = exc
    raise last_exc  # type: ignore[misc]


def extract_json(text: str) -> dict | list:
    # Try fenced code block first
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return json.loads(match.group(1))

    # Try bare JSON object or array
    for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not extract JSON from response:\n{text[:300]}")
