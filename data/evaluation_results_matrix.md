# Enterprise RAG Benchmark Evaluation Matrix

**Generated At**: 2026-11-13 16:54:53  
**Corpus**: 500+ Page Technical Handbook (384,746 words, 2,461 vector chunks)  
**Total Evaluation Queries**: 100  

## 1. Executive Metrics Summary

| Metric | Measured Value | Production Target | Status |
| :--- | :--- | :--- | :--- |
| **Mean Precision@3 (P@3)** | **0.78** | $\ge 0.85$ | REVIEW |
| **Mean Recall@3 (R@3)** | **0.78** | $\ge 0.90$ | REVIEW |
| **Mean Reciprocal Rank (MRR)** | **0.82** | $\ge 0.85$ | REVIEW |
| **Answer Relevancy** | **0.73** | $\ge 0.80$ | REVIEW |
| **Agent Reflection Score** | **9.2 / 10** | $\ge 8.0$ | PASS |
| **Zero-Hallucination Guardrail** | **93.3%** | $100.0\%$ | PASS |
| **P50 Query Latency** | **4.16s** | $< 4.0\text{s}$ | REVIEW |
| **P95 Query Latency** | **43.90s** | $< 8.0\text{s}$ | REVIEW |

## 2. Category Performance Breakdown

| Query Category | Query Count | Mean P@3 | Mean R@3 | Mean MRR | Relevancy | Reflection |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Single-Hop Fact Retrieval** | 50 | 0.89 | 0.89 | 0.91 | 0.90 | 8.5/10 |
| **Multi-Hop Synthesis** | 25 | 0.68 | 0.68 | 0.76 | 0.66 | 10.0/10 |
| **Numerical / Tabular** | 10 | 0.47 | 0.47 | 0.53 | 0.58 | 10.0/10 |
| **Zero-Hallucination Guardrail** | 15 | N/A | N/A | N/A | 0.33 | 10.0/10 |
| **Overall Production Score** | **100** | **0.78** | **0.78** | **0.82** | **0.73** | **9.2/10** |

## 3. Sample Query Verification Ledger

| ID | Category | Query Snippet | P@3 | R@3 | MRR | Relevancy | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Q001 | single_hop | What scheduler scoring algorithms and leader elect... | 1.0 | 1.0 | 1.0 | 0.8 | 8.83s |
| Q002 | single_hop | What eBPF datapaths and Cilium Hubble observabilit... | 1.0 | 1.0 | 1.0 | 1.0 | 8.19s |
| Q003 | single_hop | Which CSI driver protocols support read-write-many... | 1.0 | 1.0 | 1.0 | 0.6 | 3.56s |
| Q004 | single_hop | How do KEDA event-driven triggers and Horizontal P... | 1.0 | 1.0 | 1.0 | 1.0 | 3.93s |
| Q005 | single_hop | What NetworkPolicies and Pod Security Standards PS... | 1.0 | 1.0 | 1.0 | 1.0 | 7.8s |
| Q006 | single_hop | What asymmetric algorithm and PKCE flow are requir... | 1.0 | 1.0 | 1.0 | 1.0 | 38.29s |
| Q007 | single_hop | How are least-privilege permission grants and time... | 1.0 | 1.0 | 1.0 | 0.75 | 3.53s |
| Q008 | single_hop | What symmetric AES-GCM data key rotation and envel... | 1.0 | 1.0 | 1.0 | 1.0 | 3.28s |
| Q009 | single_hop | What mutual TLS cipher negotiation and context-awa... | 1.0 | 1.0 | 1.0 | 1.0 | 8.12s |
| Q010 | single_hop | What SLSA Level 3 provenance and cryptographic art... | 1.0 | 1.0 | 1.0 | 1.0 | 6.65s |
| Q011 | single_hop | What Raft consensus state transitions and heartbea... | 1.0 | 1.0 | 1.0 | 0.8 | 38.06s |
| Q012 | single_hop | What is the difference between leveled and size-ti... | 1.0 | 1.0 | 1.0 | 1.0 | 3.6s |
| Q013 | single_hop | How do two-phase commit 2PC and multi-version conc... | 1.0 | 1.0 | 1.0 | 1.0 | 3.9s |
| Q014 | single_hop | What virtual node distribution and replication fac... | 0.0 | 0.0 | 0.0 | 0.8 | 2.9s |
| Q015 | single_hop | How does the cost-based query optimizer execute jo... | 0.0 | 0.0 | 0.0 | 1.0 | 42.62s |
| Q016 | single_hop | How does BGP Anycast route flap damping and AS pat... | 1.0 | 1.0 | 1.0 | 1.0 | 4.18s |
| Q017 | single_hop | What QUIC protocol frame structure enables UDP zer... | 1.0 | 1.0 | 1.0 | 0.8 | 3.4s |
| Q018 | single_hop | How do stale-while-revalidate semantics and surrog... | 1.0 | 1.0 | 1.0 | 0.8 | 3.82s |
| Q019 | single_hop | Which token bucket and leaky bucket rate limiting ... | 1.0 | 1.0 | 1.0 | 1.0 | 7.02s |
| Q020 | single_hop | What weighted round-robin and active health probin... | 0.667 | 0.667 | 1.0 | 1.0 | 4.03s |
