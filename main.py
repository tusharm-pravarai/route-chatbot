"""
Minimal FastAPI chatbot for testing LLM routing between Ollama (local) and OpenAI.

Endpoints:
  POST /chat    request:  {"message": "...", "session_id": "...", "force_model": "ollama" | "openai" (optional)}
                response: {"response": "...", "model_used": "...", "route_reason": "..."}
  GET  /traces  recent routing decisions (in-memory), so it's visible which
                backend answered every request — handy for validating routing
                logic as it evolves.
  GET  /        minimal chat frontend (static/index.html)
"""
import json
import logging
import re
import time
from collections import deque
from datetime import datetime, timezone
from typing import Optional, Protocol

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config

app = FastAPI(title="Routing Test Chatbot")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("router")


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------

def load_knowledge_base() -> dict:
    with open(config.KNOWLEDGE_BASE_PATH, "r") as f:
        return json.load(f)


KNOWLEDGE_BASE = load_knowledge_base()


def kb_lookup(message: str) -> Optional[str]:
    """Look for an exact/substring match across all KB categories."""
    normalized = message.lower().strip().rstrip("?!.")
    for category in KNOWLEDGE_BASE.values():
        for key, answer in category.items():
            if key == normalized or key in normalized:
                return answer
    return None


# ---------------------------------------------------------------------------
# Model client interface — Ollama and OpenAI both implement `generate()`
# ---------------------------------------------------------------------------

class ModelClient(Protocol):
    name: str

    async def generate(self, message: str) -> str:
        ...


class OllamaClient:
    """Calls a local Ollama server's /api/generate endpoint."""

    name = "ollama"

    def __init__(self, base_url: str = config.OLLAMA_BASE_URL, model: str = config.OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model

    async def generate(self, message: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": message, "stream": False},
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()


class OpenAIClient:
    """Calls the OpenAI chat completions API."""

    name = "openai"

    def __init__(self, api_key: str = config.OPENAI_API_KEY, model: str = config.OPENAI_MODEL):
        self.api_key = api_key
        self.model = model

    async def generate(self, message: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": message}],
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()


ollama_client = OllamaClient()
openai_client = OpenAIClient()

CLIENTS = {"ollama": ollama_client, "openai": openai_client}


# ---------------------------------------------------------------------------
# Routing logic
# ---------------------------------------------------------------------------

GREETING_PATTERN = re.compile(
    r"^\s*(hi|hello|hey|good morning|good afternoon|good evening|thanks|thank you|bye|how are you)\b",
    re.IGNORECASE,
)

# Signals that a message needs heavier reasoning, coding help, or creativity —
# these are routed straight to OpenAI regardless of KB/greeting matches.
COMPLEX_KEYWORDS = (
    "code", "function", "debug", "algorithm", "write a", "explain why",
    "compare", "analyze", "design", "poem", "story", "essay", "strategy",
)


def route(message: str) -> tuple[str, str, Optional[str]]:
    """
    Decide which backend should handle `message`.

    Returns (model_name, reason, kb_answer_if_any).

    Default rule set (checked in order):
      1. Greeting / small talk           -> Ollama (cheap, low-latency, no need for a big model)
      2. Complex reasoning/coding/creative -> OpenAI (needs stronger capability)
      3. Knowledge-base factual match    -> answered directly from KB (no model call)
      4. Everything else                 -> Ollama (fallback for general queries)
    """
    if GREETING_PATTERN.search(message):
        return "ollama", "greeting/small-talk -> local model", None

    lower = message.lower()
    if any(keyword in lower for keyword in COMPLEX_KEYWORDS):
        return "openai", "complex reasoning/coding/creative -> OpenAI", None

    kb_answer = kb_lookup(message)
    if kb_answer is not None:
        return "kb", "factual query matched knowledge base -> answered directly", kb_answer

    return "ollama", "no specific match -> default to local model", None


# ---------------------------------------------------------------------------
# Tracing — records which backend answered each request so routing behavior
# is observable now, and stays observable once routing rules get smarter.
# ---------------------------------------------------------------------------

TRACES: deque = deque(maxlen=200)  # in-memory only, most recent first on read


def record_trace(session_id: str, message: str, model_used: str, reason: str, latency_ms: float) -> None:
    trace = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "message": message,
        "model_used": model_used,
        "route_reason": reason,
        "latency_ms": round(latency_ms, 1),
    }
    TRACES.appendleft(trace)
    logger.info(
        "session=%s model=%s reason=%r latency_ms=%.1f message=%r",
        session_id, model_used, reason, latency_ms, message,
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: str
    force_model: Optional[str] = None  # "ollama" or "openai", overrides routing


class ChatResponse(BaseModel):
    response: str
    model_used: str
    route_reason: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    start = time.perf_counter()

    # Explicit override lets testers force a specific backend to validate that
    # path directly, bypassing the routing rules below.
    if request.force_model in CLIENTS:
        client = CLIENTS[request.force_model]
        answer = await client.generate(request.message)
        model_used = client.name
        reason = f"forced via request.force_model={request.force_model}"
    else:
        decision, reason, kb_answer = route(request.message)
        if decision == "kb":
            answer, model_used = kb_answer, "knowledge_base"
        else:
            client = CLIENTS[decision]
            answer = await client.generate(request.message)
            model_used = client.name

    latency_ms = (time.perf_counter() - start) * 1000
    record_trace(request.session_id, request.message, model_used, reason, latency_ms)

    return ChatResponse(response=answer, model_used=model_used, route_reason=reason)


@app.get("/traces")
async def traces() -> list:
    """Recent routing decisions, most recent first. Polled by the frontend."""
    return list(TRACES)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def frontend() -> FileResponse:
    return FileResponse("static/index.html")
