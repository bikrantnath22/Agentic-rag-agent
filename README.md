# Autonomous Enterprise RAG Service

A Retrieval-Augmented Generation (RAG) system with stateful LangGraph agentic workflows, dynamic 4-tool routing, deterministic Redis caching, Prometheus observability, and automated quality self-reflection.

---

## Highlights & Verified Metrics

* **High-Throughput RAG Service**: Built a FastAPI retrieval service (Gemini Flash-Lite, ChromaDB) indexing a 500-page technical handbook (2,461 chunks); reduced repeat query latency from 4.16 s P50 to <50 ms using SHA-256 Redis caching with Prometheus metrics.
* **Agentic Multi-Tool Orchestration**: Engineered a stateful LangGraph agent with 4-tool routing (retriever, Python, math, web search) and an LLM-judged self-reflection retry loop; refused all 15 out-of-domain test queries.
* **Rigorous Evaluation**: Evaluated on 85 answerable queries across 10 domains: 0.82 MRR, 78% section-level Precision@3, and 153/153 claims judged supported by an LLM across 56 answered queries; 16 automated tests passing.

---

## Architecture Overview

```
                      ┌─────────────────────────────────────────┐
                      │            FastAPI REST API             │
                      │  /api/v1/query  |  /api/v1/ingest       │
                      │  /api/v1/health |  /metrics             │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │       LangGraph Agent Orchestrator      │
                      │               Router Node               │
                      └──────┬─────────────┬─────────────┬──────┘
                             │             │             │
              ┌──────────────┘             │             └──────────────┐
              ▼                            ▼                            ▼
     ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
     │  Retriever Node │          │ Calculator Node │          │  Code Executor  │
     │  (Dense Hybrid) │          │  (Safe Math)    │          │  (Async Python) │
     └────────┬────────┘          └────────┬────────┘          └────────┬────────┘
              │                            │                            │
              └─────────────────────┐      │      ┌─────────────────────┘
                                    ▼      ▼      ▼
                               ┌─────────────────────────┐
                               │     Generator Node      │
                               │   (Gemini Flash-Lite)   │
                               └───────────┬─────────────┘
                                           │
                                           ▼
                               ┌─────────────────────────┐
                               │     Reflection Node     │
                               │   (Quality Check Loop)  │
                               └───────────┬─────────────┘
                                           │
                         Score < 6.0 ┌─────┴─────┐ Score >= 6.0
                         (Retry)     ▼           ▼ (Complete)
                               [Regenerate]     [END]
```

### Core Architecture Components

1. **API Layer (`FastAPI`)**:
   - `/api/v1/query`: Core query endpoint with normalized SHA-256 Redis caching and timing instrumentation.
   - `/api/v1/ingest`: Supports text, directory batches, and file uploads.
   - `/api/v1/health`: Liveness and dependency checks (vector store, Redis, LLM).
   - `/metrics`: Standard Prometheus scrape endpoint (`rag_queries_total`, `rag_query_duration_seconds`, `rag_documents_retrieved`, `rag_reflection_score`).

2. **Agentic Workflow (`LangGraph`)**:
   - **Router Node**: Heuristic and rule-based intent router distinguishing arithmetic calculation, Python execution, live web search, and knowledge retrieval.
   - **Retriever Tool**: Dense semantic search with Sentence-Transformers (`all-MiniLM-L6-v2`) and BM25 sparse hybrid re-ranking.
   - **Calculator Tool**: Abstract Syntax Tree (AST) safe arithmetic evaluation.
   - **Code Executor Tool**: Sandboxed Python execution with restricted builtins namespace and 5-second `asyncio.wait_for` timeout protection.
   - **Web Search Tool**: DuckDuckGo web search integration.
   - **Reflection & Self-Correction**: Secondary evaluation step checking factual adherence. Scores below 6.0 trigger an automatic retry cycle (up to 2 iterations).

3. **Storage, Security & Observability**:
   - **Vector Database**: Pluggable storage abstraction supporting embedded ChromaDB (local development) and distributed Qdrant (`VECTOR_DB_TYPE=qdrant`).
   - **Cache**: Redis key-value cache keyed by SHA-256 hashes of `.strip().lower()` normalized queries, yielding sub-50ms repeat response times.
   - **Security**: Optional API-key and Bearer token authentication middleware (`verify_api_key`) via `AUTH_ENABLED=true`.
   - **Tracing**: Native LangSmith integration for LLM call observability via `LANGSMITH_TRACING=true`.

---

## Benchmark & Evaluation Results

The retrieval and generation pipeline was evaluated against a **100-query golden benchmark** across a synthetic **500-page enterprise handbook (391,436 words, 2,461 vector chunks)** covering 10 technical domains (Kubernetes, IAM, Distributed Databases, Edge/CDN, SLAs, FinOps, Streaming, LLM Serving, Compliance, SRE).

> **Benchmark Methodology & Corpus Note**:  
> The 500-page handbook is a structured synthetic corpus generated to benchmark retrieval mechanics, multi-hop synthesis, and tool routing across 10 controlled enterprise technical domains with deterministic ground-truth labels. The resulting metrics reflect pipeline and architectural integrity under clean, structured conditions rather than generalization across uncurated or noisy real-world documents.

### Benchmark Dataset Breakdown (100 Queries)
- **50 Single-Hop Queries**: Target single technical standards and parameters within individual document sections.
- **25 Multi-Hop Queries**: Target cross-volume synthesis connecting requirements from disparate sections.
- **10 Numerical & Tabular Queries**: Target quantitative arithmetic calculations over structured pricing and SLA tables.
- **15 Out-of-Domain Negative Queries**: Target adversarial prompts to measure refusal guardrail behavior.

*Source reports: [`data/evaluation_results_matrix.json`](file:///e:/Rag-New/multimodal-rag-agent-master/multimodal-rag-agent-master/data/evaluation_results_matrix.json) and [`data/faithfulness_results_60_queries.json`](file:///e:/Rag-New/multimodal-rag-agent-master/multimodal-rag-agent-master/data/faithfulness_results_60_queries.json)*

### Summary Metrics

| Metric | Measured Value | Target / Baseline | Notes |
| :--- | :--- | :--- | :--- |
| **Precision@3 (85 Answerable Queries)** | **0.78** (78%) | $\ge 0.70$ | Section-level ground truth across all 85 answerable queries |
| **Single-Hop Precision@3 (50 Queries)** | **0.89** (89%) | $\ge 0.85$ | Top-3 chunk relevance across 50 factual single-hop queries |
| **System MRR (85 Answerable Queries)** | **0.82** | $\ge 0.80$ | Mean Reciprocal Rank across all 85 answerable queries |
| **Single-Hop MRR** | **0.91** | $\ge 0.85$ | First relevant document at average rank 1.1 |
| **Multi-Hop MRR** | **0.76** | $\ge 0.70$ | Evaluated across 25 multi-volume synthesis queries |
| **Answer Faithfulness** | **1.00** (100%) | $\ge 0.85$ | 153/153 claims supported across 56 answered queries (0.98 in initial batch) |
| **Out-of-Domain Refusal Rate** | **100%** | $\ge 90.0\%$ | 15 of 15 adversarial negative queries rejected (14/15 in initial batch) |
| **LLM-Judged Reflection Score** | **9.2 / 10** | $\ge 8.0$ | Automated self-critique score |
| **P50 Query Latency (Cold)** | **4.16s** | $< 5.0\text{s}$ | Cold live query latency (dense retrieval + rerank + generation) |
| **Cached Query Latency** | **< 50ms** (0.02s – 0.05s) | $< 0.10\text{s}$ | Normalized SHA-256 Redis cache hit |
| **Automated Tests** | **16 passed** | 16 tests | Unit, integration, and quality test suites |

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Redis (optional; in-memory fallback enabled if offline)
- Google Gemini API Key

### 2. Local Installation

```bash
# Clone the repository
git clone <repo-url>
cd multimodal-rag-agent-master

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and set your API keys:

```bash
cp .env.example .env
```

Key environment settings in `.env`:

```ini
# LLM Configuration
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4096

# Vector Store (chroma for local embedded SQLite WAL, qdrant for service mode)
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./data/chroma
QDRANT_URL=http://localhost:6333

# Caching & Database
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./data/rag_system.db

# Observability (Optional)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=rag-agent
```

### 4. Running the API Server

```bash
# Start server with Uvicorn
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify service health:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "dependencies": {
    "vector_db": "healthy",
    "redis": "healthy",
    "llm": "configured"
  }
}
```

### 5. Running with Docker

```bash
# Build production Docker image
docker build -t rag-api:latest .

# Run containerized service with .env configuration
docker run -d -p 8000:8000 --name rag-service --env-file .env rag-api:latest
```

---

## Ingestion & Evaluation CLI

### Ingest Documents

```bash
# Generate the 500-page enterprise handbook corpus
python scripts/generate_enterprise_corpus.py

# Ingest corpus into ChromaDB
python scripts/ingest_documents.py data/enterprise_handbook_500_pages.txt --collection documents
```

### Run Evaluation Benchmarks

```bash
# Execute the 100-query benchmark against the live API endpoint
python scripts/evaluate_rag.py configs/evaluation/enterprise_100_queries.json --delay 1.0

# Audit answer faithfulness with claim-level LLM verification
python scripts/evaluate_faithfulness.py --sample-size 60
```

### Run Automated Tests

```bash
# Execute full pytest suite (16 tests)
python -m pytest tests/ -v
```

---

## API Reference

### 1. Query RAG System
`POST /api/v1/query`

**Request Body:**
```json
{
  "query": "What is the standard unit cost per vCPU-hour under FIN-COMP?",
  "top_k": 5,
  "use_reflection": true
}
```

**Response:**
```json
{
  "query": "What is the standard unit cost per vCPU-hour under FIN-COMP?",
  "answer": "Based on the provided documents, the standard unit cost for compute under operational standard FIN-COMP-0601 is $0.048 per vCPU-hour [1].",
  "documents": [
    {
      "id": "data/enterprise_handbook_500_pages.txt_1230",
      "score": 0.84,
      "content": "Clause 6.1.1 specifies the governing operational framework for compute... ($0.048 per vCPU-hour)..."
    }
  ],
  "reflection": {
    "score": 10.0,
    "feedback": "Answer accurately quotes document standard."
  },
  "metadata": {
    "cached": false
  }
}
```

### 2. Prometheus Metrics
`GET /metrics`

Scrapes live system metrics including:
- `rag_queries_total{status="success|cached|error"}`
- `rag_query_duration_seconds` (histogram)
- `rag_documents_retrieved` (histogram)
- `rag_reflection_score` (histogram)

---

## Design Decisions & Trade-Offs

1. **Embedded ChromaDB vs. Distributed Qdrant**:
   - For local development and single-node benchmarking, ChromaDB runs embedded in SQLite WAL mode with zero infrastructure overhead.
   - For multi-replica production environments, the storage layer implements an abstract `VectorStore` interface; changing `VECTOR_DB_TYPE=qdrant` switches to cluster-ready Qdrant without application code changes.

2. **Reflection & Quality Guardrails**:
   - The reflection node uses an LLM-as-a-judge critique step (`score < 6.0` triggers retry, max 2 retries). The score extractor strips markdown and handles natural language variations to eliminate spurious retries.

3. **Sandboxed Code Execution**:
   - Python code execution runs in an async thread with an explicit 5-second `asyncio.wait_for` timeout and a namespace restricted to a safe built-in whitelist (blocking file I/O, network calls, and arbitrary imports). For hostile untrusted code, microVM isolation (e.g., gVisor) is recommended.

4. **Normalized Query Caching**:
   - Queries are normalized (`.strip().lower()`) before SHA-256 hashing into Redis keys (`rag_query:{hash}`), ensuring identical queries with different casing or whitespace hit the cache in under 50ms.
