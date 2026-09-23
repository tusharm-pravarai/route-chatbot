# Routing Test Chatbot

A minimal FastAPI chatbot for testing how a request gets routed between a
local Ollama model and the OpenAI API.

## Setup

```bash
cp .env.example .env   # fill in OPENAI_API_KEY, adjust OLLAMA_MODEL if needed
./run.sh                # creates a venv, installs deps, starts uvicorn on :8000
```

Make sure Ollama is running locally (`ollama serve`) and has the model pulled
(e.g. `ollama pull llama3`) if you want to exercise the Ollama routing path.

Then open **http://localhost:8000** in a browser for the chat UI, which shows
which model answered each message and a live routing trace alongside it.

## The endpoints

`POST /chat`

```json
{
  "message": "hello there",
  "session_id": "test-1"
}
```

Response:

```json
{
  "response": "Hi there! What can I do for you?",
  "model_used": "ollama",
  "route_reason": "greeting/small-talk -> local model"
}
```

## Routing rules (default, in order)

1. **Greeting / small talk** (e.g. "hi", "thanks", "how are you") → **Ollama**
2. **Complex reasoning, coding, or creative** (message contains words like
   "code", "debug", "write a", "poem", "compare", "analyze") → **OpenAI**
3. **Factual query matching the knowledge base** → answered directly from
   `knowledge_base.json`, no model call at all
4. **Everything else** → **Ollama** (default fallback)

Every response includes `route_reason` so you can confirm which rule fired.

`GET /traces` returns the last 200 requests (most recent first) — each entry
has `session_id`, `message`, `model_used`, `route_reason`, and `latency_ms`.
This is how you see which backend is answering things without digging through
logs; the same data also streams into the "Routing Trace" panel in the UI.
Every request is also logged to the console as it happens. Traces are kept
in memory only (cleared on restart) — this is observability, not chat history.

## Testing each path explicitly

**1. Greeting → Ollama**

```bash
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "hi there", "session_id": "t1"}'
```

**2. Complex query → OpenAI**

```bash
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "write a function to reverse a linked list", "session_id": "t2"}'
```

**3. Factual query → Knowledge base**

```bash
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "what is the capital of France?", "session_id": "t3"}'
```

**4. Generic query → Ollama (fallback)**

```bash
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "tell me something", "session_id": "t4"}'
```

**5. Force a specific backend explicitly**, bypassing routing rules — useful
for isolating a single model's behavior:

```bash
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "hello", "session_id": "t5", "force_model": "openai"}'

curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "explain quantum entanglement", "session_id": "t6", "force_model": "ollama"}'
```

## Files

- `main.py` — FastAPI app, both model clients, routing logic, tracing, `/chat`/`/traces` endpoints
- `config.py` — loads settings from environment / `.env`
- `knowledge_base.json` — synthetic greetings/FAQ/facts data
- `static/index.html` — single-file chat UI (chat log + live routing trace panel)
- `.env.example` — template for required environment variables
- `run.sh` — creates a venv, installs dependencies, starts the server
