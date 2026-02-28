# research-agent — Architecture

## Overview
A minimal, extensible research agent service exposing a single HTTP API to accept research questions and return concise answers with sources.

## High-level components
- API: [app/main.py](app/main.py) and [app/api/query.py](app/api/query.py)
  - FastAPI application exposing OpenAPI docs at `/api/docs`.
  - Single POST `/api/query` endpoint that accepts a `Query` model and returns a `ResearchResponse`.

- Schemas: [app/schemas/query.py](app/schemas/query.py)
  - Pydantic models for request/response shapes. Keep models stable for API compatibility.

- Agent: [app/agents/research_agent.py](app/agents/research_agent.py)
  - Orchestrates the agentic loop: planning → executing tools → summarizing → storing in memory.
  - Keep logic small and split responsibilities: planner, executor, and result aggregator.

- Tools: [app/agents/tools.py](app/agents/tools.py)
  - Search, scrape, summarization helpers. Implement as async functions returning standardized results.
  - Design each tool to be replaceable (e.g., add Google/Bing search, local doc search, or LLM summarizer).

- Memory: [app/memory/simple_memory.py](app/memory/simple_memory.py)
  - Simple JSON-backed memory by default. Provide an implementation interface to swap to ChromaDB or other vector DBs.

- Core config: [app/core/config.py](app/core/config.py)
  - Central settings (paths, env-driven options). Use `BaseSettings` (compatible with pydantic v2/v1).

- Scripts: [scripts/test_agent.py](scripts/test_agent.py)
  - Quick local runner for iterative development.

## Data flow (POST /api/query)
1. Client POSTs `Query` to `/api/query`.
2. API handler forwards the question to `ResearchAgent.handle_question()`.
3. Agent runs toolchain:
   - Planner decides which tools to call.
   - Executor calls `search()`, `scrape()` as needed (async).
   - Summarizer condenses results into a short answer.
4. Agent stores the Q/A (and metadata) into memory.
5. API returns a `ResearchResponse` with `answer`, `sources`, and optional `used_context`.

## Extension points
- Tools: add new modules under `app/agents/tools_*.py` and register them in the agent.
- Memory: implement a `Memory` interface (methods: `add`, `all`, `query`) and provide adapters for JSON, ChromaDB, or SQLite + FAISS.
- Agents: add different agent classes if you need specialized behavior (e.g., `FactCheckingAgent`, `CrawlingAgent`).
- Auth / Rate limiting: add middleware or proxy in front of FastAPI for production.

## Recommended improvements for production
- Add Dockerfile and `docker-compose` for local testing with a vector DB service.
- Introduce async LLM summarizer with batching and rate control.
- Add logging, structured traces (OpenTelemetry), and metrics (Prometheus).
- Add tests: unit tests for `tools`, `memory` adapters, and integration tests for the API.
- Secure secrets with env vars or a secrets manager; never commit API keys.

## Running & development
- Install deps: `pip install -r requirements.txt`.
- Start development server:

```bash
uvicorn app.main:app --reload
```

- Visit OpenAPI: `http://127.0.0.1:8000/api/docs`.

## File map (quick)
- app/main.py — app bootstrap and OpenAPI settings
- app/api/query.py — HTTP endpoint
- app/schemas/query.py — Pydantic models
- app/agents/research_agent.py — agent orchestration
- app/agents/tools.py — helper tools
- app/memory/simple_memory.py — baseline memory adapter
- scripts/test_agent.py — quick developer script

## Next tasks (suggested)
- Add `Memory` abstract base class and adapter tests.
- Implement a real search tool or wire in a SERP API.
- Add integration tests for `/api/query` and run in CI.

---

If you want, I can now:
- implement a `Memory` interface and a Chroma adapter;
- add a Dockerfile and CI workflow; or
- write integration tests for the API.

Tell me which next task to do.