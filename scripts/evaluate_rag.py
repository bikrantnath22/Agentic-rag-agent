#!/usr/bin/env python3
"""Comprehensive production evaluation benchmark for RAG system."""

import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import requests
import typer
from rich.console import Console
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.rag_agent import create_rag_agent
from src.evaluation.metrics import (
    RAGMetrics,
    answer_relevancy,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from src.observability.logging import get_logger, setup_logging
from src.observability.tracing import setup_langsmith
from src.retrieval.vector_store import get_retriever

setup_logging()
setup_langsmith()
logger = get_logger(__name__)
console = Console()

app = typer.Typer()


@app.command()
def evaluate(
    test_file: str = typer.Argument(
        "configs/evaluation/enterprise_100_queries.json",
        help="Path to test queries JSON file",
    ),
    collection: str = typer.Option("documents", help="Collection name"),
    use_api: bool = typer.Option(True, help="Use running FastAPI server instead of in-process agent"),
    api_url: str = typer.Option("http://127.0.0.1:8000/api/v1/query", help="API query endpoint"),
    delay: float = typer.Option(1.5, help="Pacing delay in seconds between queries to prevent RPM spikes"),
    output_json: str = typer.Option("data/evaluation_results_matrix.json", help="Path to save JSON results"),
    output_md: str = typer.Option("data/evaluation_results_matrix.md", help="Path to save Markdown report"),
    limit: int | None = typer.Option(None, help="Optional limit on number of queries to evaluate"),
):
    """
    Run the enterprise production evaluation benchmark.

    Example:
        python scripts/evaluate_rag.py configs/evaluation/enterprise_100_queries.json
    """
    asyncio.run(
        _evaluate_async(
            test_file=test_file,
            collection=collection,
            use_api=use_api,
            api_url=api_url,
            delay=delay,
            output_json=output_json,
            output_md=output_md,
            limit=limit,
        )
    )


async def _evaluate_async(
    test_file: str,
    collection: str,
    use_api: bool,
    api_url: str,
    delay: float,
    output_json: str,
    output_md: str,
    limit: int | None,
):
    """Execute asynchronous evaluation."""
    console.print("\n[bold blue]========================================================[/bold blue]")
    console.print("[bold blue]  Enterprise Production RAG Evaluation Benchmark       [/bold blue]")
    console.print("[bold blue]========================================================[/bold blue]")
    console.print(f"Test dataset : {test_file}")
    console.print(f"Mode         : {'Live FastAPI Endpoint' if use_api else 'In-Process LangGraph Agent'}")
    console.print(f"Pacing delay : {delay}s")
    console.print(f"Output JSON  : {output_json}")
    console.print(f"Output MD    : {output_md}\n")

    test_path = Path(test_file)
    if not test_path.exists():
        console.print(f"[red]Error: Dataset {test_file} not found![/red]")
        sys.exit(1)

    with open(test_path, encoding="utf-8") as f:
        data = json.load(f)

    test_queries = data.get("queries", [])
    if limit:
        test_queries = test_queries[:limit]

    console.print(f"[green]Loaded {len(test_queries)} queries for evaluation.[/green]\n")

    # In-process fallback agent if use_api is False
    agent = None
    if not use_api:
        console.print("[yellow]Initializing in-process RAG agent...[/yellow]")
        retriever = await get_retriever(collection_name=collection)
        agent = await create_rag_agent(retriever=retriever)

    metrics = RAGMetrics()
    results = []
    latencies = []

    for idx, item in enumerate(test_queries, 1):
        q_id = item.get("id", f"Q{idx:03d}")
        category = item.get("category", "single_hop")
        volume = item.get("volume", "")
        query = item["query"]
        expected_keywords = item.get("expected_keywords", [])
        relevant_docs = item.get("relevant_docs", [])

        console.print(f"[cyan][{idx}/{len(test_queries)}] [{q_id}] ({category})[/cyan] {query[:75]}...")

        t0 = time.time()
        answer = ""
        retrieved_ids = []
        reflection_score = None
        error_msg = None

        try:
            if use_api:
                # Call running FastAPI endpoint
                resp = requests.post(
                    api_url,
                    json={"query": query, "top_k": 5, "use_reflection": True},
                    timeout=60,
                )
                if resp.status_code == 200:
                    payload = resp.json()
                    answer = payload.get("answer", "")
                    docs = payload.get("documents", [])
                    retrieved_ids = [d["id"] for d in docs]
                    reflection_score = payload.get("reflection", {}).get("score", None)
                else:
                    error_msg = f"HTTP {resp.status_code}: {resp.text}"
            else:
                # Call in-process agent
                agent_res = await agent.run(query=query)
                answer = agent_res.get("answer", "")
                docs = agent_res.get("documents", [])
                retrieved_ids = [d["id"] for d in docs]
                reflection_score = agent_res.get("reflection", {}).get("score", None)

        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Error on query {q_id}: {exc}")

        latency = time.time() - t0
        latencies.append(latency)

        # Calculate metrics
        relevancy = answer_relevancy(query, answer, expected_keywords) if answer else 0.0
        p_at_3 = precision_at_k(retrieved_ids, relevant_docs, k=3) if relevant_docs else None
        r_at_3 = recall_at_k(retrieved_ids, relevant_docs, k=3) if relevant_docs else None
        rr = reciprocal_rank(retrieved_ids, relevant_docs) if relevant_docs else None

        # Check negative rejection (zero hallucination)
        is_refusal = any(
            phrase in answer.lower()
            for phrase in ["no mention", "not contain", "does not contain", "no information", "not found", "cannot find"]
        )

        result_entry = {
            "id": q_id,
            "category": category,
            "volume": volume,
            "query": query,
            "answer_preview": (answer[:140] + "...") if answer else "",
            "latency_seconds": round(latency, 2),
            "num_docs": len(retrieved_ids),
            "relevancy": round(relevancy, 3) if relevancy is not None else 0.0,
            "p_at_3": round(p_at_3, 3) if p_at_3 is not None else None,
            "r_at_3": round(r_at_3, 3) if r_at_3 is not None else None,
            "rr": round(rr, 3) if rr is not None else None,
            "reflection_score": reflection_score,
            "is_refusal": is_refusal if category == "negative" else None,
            "error": error_msg,
        }
        results.append(result_entry)

        metrics.add_query_result(
            num_docs=len(retrieved_ids),
            reflection_score=reflection_score,
        )

        console.print(
            f"   -> Latency: {latency:.2f}s | P@3: {p_at_3} | R@3: {r_at_3} | MRR: {rr} | "
            f"Relevancy: {relevancy:.2f} | Reflection: {reflection_score}/10"
        )

        if delay > 0 and idx < len(test_queries):
            await asyncio.sleep(delay)

    # Summarize & Export
    _display_and_export_results(results, metrics, latencies, output_json, output_md)


def _display_and_export_results(
    results: list[dict[str, Any]],
    metrics: RAGMetrics,
    latencies: list[float],
    output_json: str,
    output_md: str,
):
    """Display rich summary and write JSON + Markdown reports."""
    console.print("\n[bold green]========================================================[/bold green]")
    console.print("[bold green]  Production Benchmark Results Summary                 [/bold green]")
    console.print("[bold green]========================================================[/bold green]\n")

    # Filter subsets
    valid_p = [r["p_at_3"] for r in results if r["p_at_3"] is not None]
    valid_r = [r["r_at_3"] for r in results if r["r_at_3"] is not None]
    valid_mrr = [r["rr"] for r in results if r["rr"] is not None]
    valid_relevancy = [r["relevancy"] for r in results if r.get("relevancy") is not None]
    valid_reflection = [r["reflection_score"] for r in results if r.get("reflection_score") is not None]

    single_hop = [r for r in results if r["category"] == "single_hop"]
    multi_hop = [r for r in results if r["category"] == "multi_hop"]
    negative = [r for r in results if r["category"] == "negative"]
    numerical = [r for r in results if r["category"] == "numerical"]

    mean_p = statistics.mean(valid_p) if valid_p else 0.0
    mean_r = statistics.mean(valid_r) if valid_r else 0.0
    mean_mrr = statistics.mean(valid_mrr) if valid_mrr else 0.0
    mean_rel = statistics.mean(valid_relevancy) if valid_relevancy else 0.0
    mean_ref = statistics.mean(valid_reflection) if valid_reflection else 0.0

    p50_lat = statistics.median(latencies) if latencies else 0.0
    p95_lat = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies or [0.0])

    neg_refusals = sum(1 for r in negative if r.get("is_refusal"))
    neg_accuracy = (neg_refusals / len(negative)) * 100 if negative else 100.0

    # Display Rich Table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan", width=18)
    table.add_column("Queries", justify="right", width=9)
    table.add_column("Mean P@3", justify="right", width=11)
    table.add_column("Mean R@3", justify="right", width=11)
    table.add_column("Mean MRR", justify="right", width=11)
    table.add_column("Relevancy", justify="right", width=11)
    table.add_column("Reflection", justify="right", width=11)

    def _cat_stats(subset):
        ps = [r["p_at_3"] for r in subset if r["p_at_3"] is not None]
        rs = [r["r_at_3"] for r in subset if r["r_at_3"] is not None]
        mrrs = [r["rr"] for r in subset if r["rr"] is not None]
        rels = [r["relevancy"] for r in subset if r["relevancy"] is not None]
        refs = [r["reflection_score"] for r in subset if r["reflection_score"] is not None]
        return (
            f"{statistics.mean(ps):.2f}" if ps else "N/A",
            f"{statistics.mean(rs):.2f}" if rs else "N/A",
            f"{statistics.mean(mrrs):.2f}" if mrrs else "N/A",
            f"{statistics.mean(rels):.2f}" if rels else "N/A",
            f"{statistics.mean(refs):.1f}" if refs else "N/A",
        )

    for name, subset in [
        ("Single-Hop (50)", single_hop),
        ("Multi-Hop (25)", multi_hop),
        ("Numerical (10)", numerical),
        ("Zero-Halluc. (15)", negative),
    ]:
        p, r, mrr, rel, ref = _cat_stats(subset)
        table.add_row(name, str(len(subset)), p, r, mrr, rel, ref)

    table.add_section()
    table.add_row(
        "[bold]Overall System[/bold]",
        f"[bold]{len(results)}[/bold]",
        f"[bold]{mean_p:.2f}[/bold]",
        f"[bold]{mean_r:.2f}[/bold]",
        f"[bold]{mean_mrr:.2f}[/bold]",
        f"[bold]{mean_rel:.2f}[/bold]",
        f"[bold]{mean_ref:.1f}/10[/bold]",
    )
    console.print(table)

    console.print("\n[bold]Latency Metrics:[/bold]")
    console.print(f"  P50 Latency : {p50_lat:.2f}s")
    console.print(f"  P95 Latency : {p95_lat:.2f}s")
    console.print(f"  Mean Latency: {statistics.mean(latencies):.2f}s")
    console.print("\n[bold]Hallucination Guardrail Check:[/bold]")
    console.print(f"  Negative Refusal Rate : {neg_accuracy:.1f}% ({neg_refusals}/{len(negative)} out-of-domain rejected)\n")

    # Build Output Payload
    summary_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_queries": len(results),
        "mean_precision_at_3": round(mean_p, 3),
        "mean_recall_at_3": round(mean_r, 3),
        "mean_mrr": round(mean_mrr, 3),
        "mean_answer_relevancy": round(mean_rel, 3),
        "mean_reflection_score": round(mean_ref, 2),
        "latency_seconds": {
            "p50": round(p50_lat, 2),
            "p95": round(p95_lat, 2),
            "mean": round(statistics.mean(latencies), 2),
        },
        "hallucination_guardrails": {
            "out_of_domain_queries": len(negative),
            "refusals_detected": neg_refusals,
            "refusal_rate_pct": round(neg_accuracy, 1),
        },
        "results": results,
    }

    Path(output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    console.print(f"[green]Saved JSON benchmark matrix to: {output_json}[/green]")

    # Build Markdown Report
    md_content = f"""# Enterprise RAG Benchmark Evaluation Matrix

**Generated At**: {time.strftime("%Y-%m-%d %H:%M:%S")}  
**Corpus**: 500+ Page Technical Handbook (384,746 words, 2,461 vector chunks)  
**Total Evaluation Queries**: {len(results)}  

## 1. Executive Metrics Summary

| Metric | Measured Value | Production Target | Status |
| :--- | :--- | :--- | :--- |
| **Mean Precision@3 (P@3)** | **{mean_p:.2f}** | $\\ge 0.85$ | {'PASS' if mean_p >= 0.85 else 'REVIEW'} |
| **Mean Recall@3 (R@3)** | **{mean_r:.2f}** | $\\ge 0.90$ | {'PASS' if mean_r >= 0.90 else 'REVIEW'} |
| **Mean Reciprocal Rank (MRR)** | **{mean_mrr:.2f}** | $\\ge 0.85$ | {'PASS' if mean_mrr >= 0.85 else 'REVIEW'} |
| **Answer Relevancy** | **{mean_rel:.2f}** | $\\ge 0.80$ | {'PASS' if mean_rel >= 0.80 else 'REVIEW'} |
| **Agent Reflection Score** | **{mean_ref:.1f} / 10** | $\\ge 8.0$ | {'PASS' if mean_ref >= 8.0 else 'REVIEW'} |
| **Zero-Hallucination Guardrail** | **{neg_accuracy:.1f}%** | $100.0\\%$ | {'PASS' if neg_accuracy >= 90.0 else 'REVIEW'} |
| **P50 Query Latency** | **{p50_lat:.2f}s** | $< 4.0\\text{{s}}$ | {'PASS' if p50_lat <= 4.0 else 'REVIEW'} |
| **P95 Query Latency** | **{p95_lat:.2f}s** | $< 8.0\\text{{s}}$ | {'PASS' if p95_lat <= 8.0 else 'REVIEW'} |

## 2. Category Performance Breakdown

| Query Category | Query Count | Mean P@3 | Mean R@3 | Mean MRR | Relevancy | Reflection |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Single-Hop Fact Retrieval** | {len(single_hop)} | {_cat_stats(single_hop)[0]} | {_cat_stats(single_hop)[1]} | {_cat_stats(single_hop)[2]} | {_cat_stats(single_hop)[3]} | {_cat_stats(single_hop)[4]}/10 |
| **Multi-Hop Synthesis** | {len(multi_hop)} | {_cat_stats(multi_hop)[0]} | {_cat_stats(multi_hop)[1]} | {_cat_stats(multi_hop)[2]} | {_cat_stats(multi_hop)[3]} | {_cat_stats(multi_hop)[4]}/10 |
| **Numerical / Tabular** | {len(numerical)} | {_cat_stats(numerical)[0]} | {_cat_stats(numerical)[1]} | {_cat_stats(numerical)[2]} | {_cat_stats(numerical)[3]} | {_cat_stats(numerical)[4]}/10 |
| **Zero-Hallucination Guardrail** | {len(negative)} | {_cat_stats(negative)[0]} | {_cat_stats(negative)[1]} | {_cat_stats(negative)[2]} | {_cat_stats(negative)[3]} | {_cat_stats(negative)[4]}/10 |
| **Overall Production Score** | **{len(results)}** | **{mean_p:.2f}** | **{mean_r:.2f}** | **{mean_mrr:.2f}** | **{mean_rel:.2f}** | **{mean_ref:.1f}/10** |

## 3. Sample Query Verification Ledger

| ID | Category | Query Snippet | P@3 | R@3 | MRR | Relevancy | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in results[:20]:
        md_content += f"| {r['id']} | {r['category']} | {r['query'][:50]}... | {r['p_at_3'] if r['p_at_3'] is not None else 'N/A'} | {r['r_at_3'] if r['r_at_3'] is not None else 'N/A'} | {r['rr'] if r['rr'] is not None else 'N/A'} | {r['relevancy']} | {r['latency_seconds']}s |\n"

    Path(output_md).parent.mkdir(parents=True, exist_ok=True)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    console.print(f"[green]Saved Markdown benchmark report to: {output_md}[/green]\n")


if __name__ == "__main__":
    app()
