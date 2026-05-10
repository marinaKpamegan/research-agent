# 🚀 AI Research Agent: Multi-Expert Grounding System

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://python.langchain.com/docs/langgraph)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-green.svg)](https://fastapi.tiangolo.com/)

## 💼 The Business Problem: The Quest for Truth in the Age of Information Overload
**"In a world saturated with information, the speed of access to verifiable data is a strategic advantage."**

Experts (researchers, data scientists, public decision-makers) face a triple challenge that generalist LLMs cannot solve alone:

1.  **Data Fragmentation**: Technical information is scattered. An academic paper is on **ArXiv**, while its implementation and benchmarks are on **PapersWithCode**. Manually crossing these two sources is tedious.
2.  **The Trust Paradox (Hallucinations)**: "Standard" LLMs tend to invent facts to appear coherent. For high-stakes decisions (technological investments, scientific research), uncertainty is unacceptable.
3.  **Access to Public Data**: LLMs lack direct and structured access to official datasets (e.g., Data.gouv.fr), making administrative or budgetary research imprecise.

### 💡 The Solution: Research Agent
**Research Agent** transforms this process into an automated and intelligent workflow:
- **Scientific Parallelization**: For research queries, it simultaneously queries **ArXiv** and **PapersWithCode**, merging theory and code into a single asynchronous stream.
- **Grounding on Real Data**: Every claim is linked to a real source retrieved via specialized APIs or the MCP protocol.
- **Productivity Gain**: What used to take 30 minutes of browsing between different tabs is reduced to a structured synthesis in seconds.

---

## 🏗️ Backend Engineering & Architecture

The heart of the system is a complex state graph developed with **LangGraph**, designed for performance and precision.

### ⚡ Scientific Parallelism (Fan-out/Fan-in)
For queries identified as "Science" by the LLM router, the backend triggers parallel execution:
- **ArXiv Node**: Extraction of academic publications via the ArXiv API.
- **PapersWithCode Node**: Search for GitHub implementations and benchmarks.
This architecture halves the response time and enables a rich synthesis (Theory + Code).

### 🏛️ Data.gouv Integration via MCP
The agent uses the **Model Context Protocol (MCP)** to dynamically query French government APIs.
- **Dynamic Tooling**: On-the-fly argument cleaning to ensure the stability of API calls.
- **Statistics Retrieval**: Ability to extract precise figures (e.g., ministerial budgets) directly from official datasets.

### 🔍 Hybrid RAG & Asynchronous Vision
- **Intelligent Scraping**: Using **Crawl4AI** to transform complex web pages into clean Markdown.
- **Vector Search**: Ephemeral local storage in **FAISS** for precise contextual RAG on freshly crawled content.

---

## ✨ Production-Oriented Features

### 📡 Granular Streaming (SSE)
The interface doesn't just "load" into a vacuum. The backend streams in real-time via Server-Sent Events:
- **Reasoning Panel**: The agent's thinking steps.
- **Status Events**: Source selection, start of parallel searches, etc.

### 🛡️ Robustness & Observability
- **Recursion Guard**: Graph depth limit to avoid infinite loops on complex searches.
- **RAGAS Evaluation**: Integrated pipeline to measure response faithfulness relative to the extracted context (TODO)

---

## 🛠️ Technical Stack

- **Framework**: FastAPI (Python 3.12)
- **Intelligence**: LangGraph, LangChain, OpenRouter (Gemini 2.5 Flash)
- **Data & Search**: SearXNG (Web), MCP (Data.gouv), ArXiv, PapersWithCode
- **Parsing & Vector**: Crawl4AI, FAISS, PostgreSQL
- **Monitoring**: Ragas (Quality evaluation)

---

## ⚙️ Installation & Local Launch

### 1. Prerequisites
- Python 3.12+
- PostgreSQL
- SearXNG instance (or access to a remote instance)

### 2. Installation
```bash
git clone https://github.com/marinaKpamegan/research-agent
cd research-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration (Environment Variables)
Create a `.env` file at the root:
```env
# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/researchagent

# LLM APIs
OPENROUTER_API_KEY=your_openrouter_key

# Services
SEARXNG_URL=http://your-searxng-instance:8080
MCP_SERVER=https://mcp.data.gouv.fr/mcp

# Auth
SECRET_KEY=your_jwt_secret_key
```

### 4. Database Initialization
Execute the `init.sql` file on PostgreSQL.

### 5. Start the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📂 Code Structure

- `app/api`: FastAPI endpoints (auth, query, preferences).
- `app/agents`: Core agentic logic and LangGraph definition.
- `app/services`: Third-party services (ArXiv, PWC, PDF Visual, SearXNG, Crawl4AI).
- `app/db`: SQLAlchemy models and repositories.
- `app/schemas`: Pydantic models for API validation.

---

## 📄 License
[MIT](LICENSE)
