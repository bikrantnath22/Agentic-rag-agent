#!/usr/bin/env python3
"""Generate the golden evaluation benchmark dataset with 100 enterprise queries."""

import json
from pathlib import Path

import chromadb

OUTPUT_FILE = Path("configs/evaluation/enterprise_100_queries.json")

# Define the 100 benchmark queries
QUERY_SPECS = [
    # =========================================================================
    # Category A: 50 Single-Hop Queries (5 per volume across all 10 volumes)
    # =========================================================================
    # Volume 1: Cloud Infrastructure & Kubernetes Architecture
    {
        "id": "Q001",
        "category": "single_hop",
        "volume": "Volume 1",
        "query": "What scheduler scoring algorithms and leader election lease mechanisms govern the Kubernetes control plane?",
        "expected_keywords": ["scheduler", "scoring", "leader election", "leases", "etcd"],
        "search_term": "K8S-CTRL"
    },
    {
        "id": "Q002",
        "category": "single_hop",
        "volume": "Volume 1",
        "query": "What eBPF datapaths and Cilium Hubble observability tools are used for container networking?",
        "expected_keywords": ["eBPF", "Cilium", "Hubble", "mTLS", "datapaths"],
        "search_term": "K8S-NET"
    },
    {
        "id": "Q003",
        "category": "single_hop",
        "volume": "Volume 1",
        "query": "Which CSI driver protocols support read-write-many NFS access modes and dynamic volume snapshots?",
        "expected_keywords": ["CSI", "snapshots", "read-write-many", "NFS", "provisioning"],
        "search_term": "K8S-STOR"
    },
    {
        "id": "Q004",
        "category": "single_hop",
        "volume": "Volume 1",
        "query": "How do KEDA event-driven triggers and Horizontal Pod Autoscaler HPA metrics profile workloads?",
        "expected_keywords": ["KEDA", "HPA", "autoscaler", "metrics", "workload"],
        "search_term": "K8S-AUTO"
    },
    {
        "id": "Q005",
        "category": "single_hop",
        "volume": "Volume 1",
        "query": "What NetworkPolicies and Pod Security Standards PSS enforce multi-tenancy namespace isolation?",
        "expected_keywords": ["NetworkPolicies", "Pod Security Standards", "PSS", "ResourceQuotas", "isolation"],
        "search_term": "K8S-ISO"
    },

    # Volume 2: Enterprise Security, Zero-Trust Architecture & IAM
    {
        "id": "Q006",
        "category": "single_hop",
        "volume": "Volume 2",
        "query": "What asymmetric algorithm and PKCE flow are required for enterprise JWT token cryptography?",
        "expected_keywords": ["OAuth 2.0", "PKCE", "JWT", "RS256", "cryptography"],
        "search_term": "SEC-IAM"
    },
    {
        "id": "Q007",
        "category": "single_hop",
        "volume": "Volume 2",
        "query": "How are least-privilege permission grants and time-bound break-glass access enforced in RBAC?",
        "expected_keywords": ["least-privilege", "break-glass", "RBAC", "role assumption"],
        "search_term": "SEC-RBAC"
    },
    {
        "id": "Q008",
        "category": "single_hop",
        "volume": "Volume 2",
        "query": "What symmetric AES-GCM data key rotation and envelope cryptography are mandated by KMS?",
        "expected_keywords": ["KMS", "envelope", "AES-GCM", "CMEK", "HSM"],
        "search_term": "SEC-KMS"
    },
    {
        "id": "Q009",
        "category": "single_hop",
        "volume": "Volume 2",
        "query": "What mutual TLS cipher negotiation and context-aware access proxies define Zero-Trust Network Access?",
        "expected_keywords": ["Zero-Trust", "ZTNA", "mTLS", "cipher", "microsegmentation"],
        "search_term": "SEC-ZTNA"
    },
    {
        "id": "Q010",
        "category": "single_hop",
        "volume": "Volume 2",
        "query": "What SLSA Level 3 provenance and cryptographic artifact signing with Cosign are required for images?",
        "expected_keywords": ["SLSA", "Cosign", "provenance", "SBOM", "CVE"],
        "search_term": "SEC-SUPP"
    },

    # Volume 3: Distributed Database Internals & Storage Engines
    {
        "id": "Q011",
        "category": "single_hop",
        "volume": "Volume 3",
        "query": "What Raft consensus state transitions and heartbeat timeouts mitigate split-brain conditions?",
        "expected_keywords": ["Raft", "consensus", "heartbeat", "split-brain", "replication"],
        "search_term": "DB-CONS"
    },
    {
        "id": "Q012",
        "category": "single_hop",
        "volume": "Volume 3",
        "query": "What is the difference between leveled and size-tiered compaction in LSM-tree memtables and SSTables?",
        "expected_keywords": ["LSM-tree", "memtables", "SSTables", "compaction", "leveled"],
        "search_term": "DB-ENG"
    },
    {
        "id": "Q013",
        "category": "single_hop",
        "volume": "Volume 3",
        "query": "How do two-phase commit 2PC and multi-version concurrency control MVCC prevent serializable ACID anomalies?",
        "expected_keywords": ["two-phase commit", "2PC", "MVCC", "concurrency", "isolation"],
        "search_term": "DB-TXN"
    },
    {
        "id": "Q014",
        "category": "single_hop",
        "volume": "Volume 3",
        "query": "What virtual node distribution and replication factor RF=3 write quorums ensure data partitioning?",
        "expected_keywords": ["virtual node", "partitioning", "RF=3", "quorums", "Merkle"],
        "search_term": "DB-PART"
    },
    {
        "id": "Q015",
        "category": "single_hop",
        "volume": "Volume 3",
        "query": "How does the cost-based query optimizer execute join pushdown and columnar projection pushdown?",
        "expected_keywords": ["optimizer", "pushdown", "columnar", "projection", "join"],
        "search_term": "DB-OPT"
    },

    # Volume 4: Network Protocols, Edge CDN & Routing
    {
        "id": "Q016",
        "category": "single_hop",
        "volume": "Volume 4",
        "query": "How does BGP Anycast route flap damping and AS path selection route traffic to edge nodes?",
        "expected_keywords": ["BGP", "Anycast", "route flap", "GeoDNS", "ECMP"],
        "search_term": "NET-BGP"
    },
    {
        "id": "Q017",
        "category": "single_hop",
        "volume": "Volume 4",
        "query": "What QUIC protocol frame structure enables UDP zero-RTT connection resumption in HTTP/3?",
        "expected_keywords": ["HTTP/3", "QUIC", "zero-RTT", "UDP", "head-of-line"],
        "search_term": "NET-H3"
    },
    {
        "id": "Q018",
        "category": "single_hop",
        "volume": "Volume 4",
        "query": "How do stale-while-revalidate semantics and surrogate keys manage targeted edge cache purging?",
        "expected_keywords": ["stale-while-revalidate", "surrogate keys", "caching", "purging", "edge"],
        "search_term": "NET-CDN"
    },
    {
        "id": "Q019",
        "category": "single_hop",
        "volume": "Volume 4",
        "query": "Which token bucket and leaky bucket rate limiting algorithms protect upstream scrubbing centers from DDoS?",
        "expected_keywords": ["token bucket", "leaky bucket", "rate limiting", "DDoS", "scrubbing"],
        "search_term": "NET-DDOS"
    },
    {
        "id": "Q020",
        "category": "single_hop",
        "volume": "Volume 4",
        "query": "What weighted round-robin and active health probing strategies govern global load balancing traffic splitting?",
        "expected_keywords": ["round-robin", "load balancing", "canary", "failover", "probing"],
        "search_term": "NET-GLB"
    },

    # Volume 5: Disaster Recovery, High Availability & SLAs
    {
        "id": "Q021",
        "category": "single_hop",
        "volume": "Volume 5",
        "query": "What Recovery Time Objective RTO and Recovery Point Objective RPO limits classify DR tiers?",
        "expected_keywords": ["RTO", "RPO", "Recovery Time Objective", "standby", "disaster"],
        "search_term": "HA-RTO"
    },
    {
        "id": "Q022",
        "category": "single_hop",
        "volume": "Volume 5",
        "query": "How do Conflict-Free Replicated Data Types CRDT maintain active-active multi-region synchronization?",
        "expected_keywords": ["CRDT", "replication", "clock drift", "multi-region", "synchronization"],
        "search_term": "HA-A2A"
    },
    {
        "id": "Q023",
        "category": "single_hop",
        "volume": "Volume 5",
        "query": "What fault injection experiments and bulkhead isolation patterns are executed in chaos engineering?",
        "expected_keywords": ["chaos", "fault injection", "bulkhead", "latency", "resilience"],
        "search_term": "HA-CHAOS"
    },
    {
        "id": "Q024",
        "category": "single_hop",
        "volume": "Volume 5",
        "query": "How is four nines 99.99% availability calculated against monthly error budget burn rates?",
        "expected_keywords": ["99.99%", "error budget", "burn rates", "availability", "SLA"],
        "search_term": "HA-SLA"
    },
    {
        "id": "Q025",
        "category": "single_hop",
        "volume": "Volume 5",
        "query": "What WORM object storage immutability and encrypted air-gapped snapshots protect backup strategies?",
        "expected_keywords": ["WORM", "immutability", "snapshots", "PITR", "backup"],
        "search_term": "HA-BAK"
    },

    # Volume 6: Enterprise Financial Policies, Billing & Pricing
    {
        "id": "Q026",
        "category": "single_hop",
        "volume": "Volume 6",
        "query": "What is the unit cost for Standard tier compute per vCPU-hour and High-Memory tier per GB-hour?",
        "expected_keywords": ["$0.048", "vCPU-hour", "$0.092", "GB-hour", "compute"],
        "search_term": "FIN-COMP"
    },
    {
        "id": "Q027",
        "category": "single_hop",
        "volume": "Volume 6",
        "query": "What are the storage rates for Hot tier ($0.021) and Cold archive storage ($0.004) per GB-month?",
        "expected_keywords": ["$0.021", "$0.004", "GB-month", "Hot tier", "Cold archive"],
        "search_term": "FIN-STOR"
    },
    {
        "id": "Q028",
        "category": "single_hop",
        "volume": "Volume 6",
        "query": "What enterprise invoice credit percentages apply when uptime falls below 99.9%, 99.0%, and 95.0%?",
        "expected_keywords": ["10%", "25%", "100%", "invoice credit", "uptime"],
        "search_term": "FIN-CRED"
    },
    {
        "id": "Q029",
        "category": "single_hop",
        "volume": "Volume 6",
        "query": "What volume licensing discounts apply to Tier 2 (10-50TB) and Tier 3 (50-250TB) storage?",
        "expected_keywords": ["12%", "22%", "Tier 2", "Tier 3", "discount"],
        "search_term": "FIN-VOL"
    },
    {
        "id": "Q030",
        "category": "single_hop",
        "volume": "Volume 6",
        "query": "At what percentage thresholds are automated budget alerts triggered under FinOps governance?",
        "expected_keywords": ["75%", "90%", "100%", "budget alerts", "FinOps"],
        "search_term": "FIN-TAG"
    },

    # Volume 7: Data Engineering & Real-Time Streaming
    {
        "id": "Q031",
        "category": "single_hop",
        "volume": "Volume 7",
        "query": "How do idempotent producers and consumer group rebalancing protocols ensure Kafka exactly-once processing EOS?",
        "expected_keywords": ["Kafka", "idempotent", "exactly-once", "EOS", "consumer group"],
        "search_term": "STR-KAFKA"
    },
    {
        "id": "Q032",
        "category": "single_hop",
        "volume": "Volume 7",
        "query": "What RocksDB state backend checkpointing and Chandy-Lamport distributed snapshot algorithms are used in Flink?",
        "expected_keywords": ["Flink", "RocksDB", "Chandy-Lamport", "snapshot", "watermark"],
        "search_term": "STR-FLINK"
    },
    {
        "id": "Q033",
        "category": "single_hop",
        "volume": "Volume 7",
        "query": "What Parquet columnar encoding and write-audit-publish patterns support lakehouse ACID transactions?",
        "expected_keywords": ["Parquet", "lakehouse", "ACID", "write-audit-publish", "columnar"],
        "search_term": "STR-LAKE"
    },
    {
        "id": "Q034",
        "category": "single_hop",
        "volume": "Volume 7",
        "query": "How do Avro schema compatibility and Dead Letter Queue DLQ routing enforce data quality validation?",
        "expected_keywords": ["Avro", "DLQ", "Dead Letter Queue", "schema", "compatibility"],
        "search_term": "STR-QUAL"
    },
    {
        "id": "Q035",
        "category": "single_hop",
        "volume": "Volume 7",
        "query": "How does batch ETL orchestration handle backfill concurrency controls and idempotent pipeline restarts?",
        "expected_keywords": ["ETL", "DAG", "backfill", "idempotent", "lineage"],
        "search_term": "STR-DAG"
    },

    # Volume 8: Machine Learning Infrastructure & LLM Serving
    {
        "id": "Q036",
        "category": "single_hop",
        "volume": "Volume 8",
        "query": "How does vLLM PagedAttention virtual memory allocation and continuous batching optimize LLM serving?",
        "expected_keywords": ["vLLM", "PagedAttention", "continuous batching", "KV-cache", "memory"],
        "search_term": "ML-SERV"
    },
    {
        "id": "Q037",
        "category": "single_hop",
        "volume": "Volume 8",
        "query": "What Megatron-style tensor parallelism and ZeRO stage-3 parameter sharding are used across GPU ranks?",
        "expected_keywords": ["Megatron", "tensor parallelism", "ZeRO", "GPU", "NCCL"],
        "search_term": "ML-PARA"
    },
    {
        "id": "Q038",
        "category": "single_hop",
        "volume": "Volume 8",
        "query": "What AWQ activation-aware quantization and FlashAttention-2 GPU kernels optimize model inference?",
        "expected_keywords": ["AWQ", "FlashAttention-2", "quantization", "FP8", "kernels"],
        "search_term": "ML-QUANT"
    },
    {
        "id": "Q039",
        "category": "single_hop",
        "volume": "Volume 8",
        "query": "What Hierarchical Navigable Small World HNSW graphs and product quantization PQ index vector search?",
        "expected_keywords": ["HNSW", "vector", "ANN", "product quantization", "cosine"],
        "search_term": "ML-VEC"
    },
    {
        "id": "Q040",
        "category": "single_hop",
        "volume": "Volume 8",
        "query": "What Wasserstein distance metrics detect embedding drift and monitor token latency percentiles?",
        "expected_keywords": ["Wasserstein", "drift", "latency", "p95", "monitoring"],
        "search_term": "ML-EVAL"
    },

    # Volume 9: Legal, Compliance & Regulatory Standards
    {
        "id": "Q041",
        "category": "single_hop",
        "volume": "Volume 9",
        "query": "What Article 17 right to erasure timeframe and DPIA triggers govern GDPR compliance?",
        "expected_keywords": ["GDPR", "Article 17", "erasure", "30 days", "DPIA"],
        "search_term": "REG-GDPR"
    },
    {
        "id": "Q042",
        "category": "single_hop",
        "volume": "Volume 9",
        "query": "What ePHI encryption mandates and 6-year audit trail retention are required under HIPAA Security Rules?",
        "expected_keywords": ["HIPAA", "ePHI", "encryption", "6-year", "BAA"],
        "search_term": "REG-HIPAA"
    },
    {
        "id": "Q043",
        "category": "single_hop",
        "volume": "Volume 9",
        "query": "What five Trust Services Criteria are audited under SOC 2 Type II continuous evidence collection?",
        "expected_keywords": ["SOC 2", "Trust Services", "Security", "Availability", "Confidentiality"],
        "search_term": "REG-SOC2"
    },
    {
        "id": "Q044",
        "category": "single_hop",
        "volume": "Volume 9",
        "query": "What PCI-DSS requirement 3 tokenization and requirement 10 automated logging protect cardholder data?",
        "expected_keywords": ["PCI-DSS", "tokenization", "cardholder", "requirement 3", "logging"],
        "search_term": "REG-PCI"
    },
    {
        "id": "Q045",
        "category": "single_hop",
        "volume": "Volume 9",
        "query": "What SEC Rule 17a-4 non-rewritable non-erasable storage format governs 7-year financial record retention?",
        "expected_keywords": ["SEC Rule 17a-4", "non-erasable", "7-year", "retention", "legal hold"],
        "search_term": "REG-SEC17"
    },

    # Volume 10: SRE Protocols, Incident Response & Runbooks
    {
        "id": "Q046",
        "category": "single_hop",
        "volume": "Volume 10",
        "query": "What response SLAs define SEV-1, SEV-2, and SEV-3 incidents in the severity classification matrix?",
        "expected_keywords": ["SEV-1", "15-minute", "SEV-2", "30-minute", "SEV-3"],
        "search_term": "SRE-SEV"
    },
    {
        "id": "Q047",
        "category": "single_hop",
        "volume": "Volume 10",
        "query": "After how many minutes is an unacknowledged on-call alert automatically escalated?",
        "expected_keywords": ["5 minutes", "on-call", "escalation", "rotation", "handover"],
        "search_term": "SRE-CALL"
    },
    {
        "id": "Q048",
        "category": "single_hop",
        "volume": "Volume 10",
        "query": "Within how many hours must a blameless post-mortem be published following incident resolution?",
        "expected_keywords": ["72 hours", "post-mortem", "blameless", "5-Whys", "root cause"],
        "search_term": "SRE-POST"
    },
    {
        "id": "Q049",
        "category": "single_hop",
        "volume": "Volume 10",
        "query": "What Golden Signals and OpenTelemetry span propagation telemetry are tracked on SRE dashboards?",
        "expected_keywords": ["Golden Signals", "latency", "traffic", "errors", "OpenTelemetry"],
        "search_term": "SRE-OBS"
    },
    {
        "id": "Q050",
        "category": "single_hop",
        "volume": "Volume 10",
        "query": "What progressive traffic shifting percentages (5% -> 25% -> 100%) govern production canary rollouts?",
        "expected_keywords": ["canary", "5%", "25%", "100%", "traffic shifting"],
        "search_term": "SRE-REL"
    },

    # =========================================================================
    # Category B: 25 Multi-Hop Synthesis Queries
    # =========================================================================
    {
        "id": "Q051",
        "category": "multi_hop",
        "volume": "Volume 5 & 10",
        "query": "How do Recovery Time Objective RTO thresholds in Disaster Recovery align with SEV-1 incident response SLAs?",
        "expected_keywords": ["RTO", "SEV-1", "15-minute", "failover", "downtime"],
        "search_terms": ["HA-RTO", "SRE-SEV"]
    },
    {
        "id": "Q052",
        "category": "multi_hop",
        "volume": "Volume 2 & 9",
        "query": "Compare the KMS 256-bit AES-GCM envelope cryptography with HIPAA ePHI encryption mandates for data at rest.",
        "expected_keywords": ["AES-GCM", "envelope", "HIPAA", "ePHI", "encryption"],
        "search_terms": ["SEC-KMS", "REG-HIPAA"]
    },
    {
        "id": "Q053",
        "category": "multi_hop",
        "volume": "Volume 1 & 2",
        "query": "How do Kubernetes Pod Security Standards PSS and NetworkPolicies support Zero-Trust microsegmentation?",
        "expected_keywords": ["PSS", "NetworkPolicies", "Zero-Trust", "microsegmentation", "isolation"],
        "search_terms": ["K8S-ISO", "SEC-ZTNA"]
    },
    {
        "id": "Q054",
        "category": "multi_hop",
        "volume": "Volume 6 & 7",
        "query": "What are the storage cost implications of lakehouse write-audit-publish patterns under Hot vs Cold storage pricing?",
        "expected_keywords": ["Hot tier", "Cold archive", "$0.021", "$0.004", "write-audit-publish"],
        "search_terms": ["FIN-STOR", "STR-LAKE"]
    },
    {
        "id": "Q055",
        "category": "multi_hop",
        "volume": "Volume 1 & 8",
        "query": "How do Kubernetes memory quota allocations in Section 1.5 interface with vLLM PagedAttention virtual memory KV-cache?",
        "expected_keywords": ["ResourceQuotas", "vLLM", "PagedAttention", "KV-cache", "memory"],
        "search_terms": ["K8S-ISO", "ML-SERV"]
    },
    {
        "id": "Q056",
        "category": "multi_hop",
        "volume": "Volume 3 & 4",
        "query": "How do distributed database Raft consensus heartbeats compare to BGP Anycast route flap damping during network degradation?",
        "expected_keywords": ["Raft", "heartbeat", "BGP", "Anycast", "split-brain"],
        "search_terms": ["DB-CONS", "NET-BGP"]
    },
    {
        "id": "Q057",
        "category": "multi_hop",
        "volume": "Volume 5 & 6",
        "query": "Synthesize the financial refund credits for uptime degradation below 95% with monthly error budget burn rates.",
        "expected_keywords": ["100%", "invoice credit", "error budget", "burn rates", "SLA"],
        "search_terms": ["FIN-CRED", "HA-SLA"]
    },
    {
        "id": "Q058",
        "category": "multi_hop",
        "volume": "Volume 9 & 10",
        "query": "How do SOC 2 Type II continuous evidence collection requirements correlate with OpenTelemetry distributed tracing spans?",
        "expected_keywords": ["SOC 2", "evidence", "OpenTelemetry", "tracing", "audit"],
        "search_terms": ["REG-SOC2", "SRE-OBS"]
    },
    {
        "id": "Q059",
        "category": "multi_hop",
        "volume": "Volume 1 & 4",
        "query": "Compare the rate limiting leaky bucket algorithms at edge CDN scrubbers with API server rate limiting in the Kubernetes control plane.",
        "expected_keywords": ["leaky bucket", "rate limiting", "control plane", "API server", "DDoS"],
        "search_terms": ["NET-DDOS", "K8S-CTRL"]
    },
    {
        "id": "Q060",
        "category": "multi_hop",
        "volume": "Volume 3 & 6",
        "query": "What are the network egress cost consequences of maintaining replication factor RF=3 write quorums across regions?",
        "expected_keywords": ["RF=3", "egress", "$0.02", "cross-region", "quorum"],
        "search_terms": ["DB-PART", "FIN-STOR"]
    },
    {
        "id": "Q061",
        "category": "multi_hop",
        "volume": "Volume 5 & 9",
        "query": "How do immutable WORM backup storage snapshots fulfill SEC Rule 17a-4 non-erasable record requirements?",
        "expected_keywords": ["WORM", "immutability", "SEC Rule 17a-4", "non-erasable", "backup"],
        "search_terms": ["HA-BAK", "REG-SEC17"]
    },
    {
        "id": "Q062",
        "category": "multi_hop",
        "volume": "Volume 1 & 7",
        "query": "How do KEDA event-driven autoscaling triggers coordinate with Kafka consumer group partition rebalancing?",
        "expected_keywords": ["KEDA", "autoscaler", "Kafka", "consumer group", "rebalancing"],
        "search_terms": ["K8S-AUTO", "STR-KAFKA"]
    },
    {
        "id": "Q063",
        "category": "multi_hop",
        "volume": "Volume 2 & 4",
        "query": "Contrast OAuth 2.0 PKCE user authorization with mutual TLS mTLS cipher negotiation across internal edge proxies.",
        "expected_keywords": ["OAuth 2.0", "PKCE", "mTLS", "cipher", "Zero-Trust"],
        "search_terms": ["SEC-IAM", "SEC-ZTNA"]
    },
    {
        "id": "Q064",
        "category": "multi_hop",
        "volume": "Volume 3 & 7",
        "query": "How does the cost-based query optimizer leverage Parquet columnar dictionary compression for projection pushdown?",
        "expected_keywords": ["query optimizer", "Parquet", "columnar", "projection pushdown", "compression"],
        "search_terms": ["DB-OPT", "STR-LAKE"]
    },
    {
        "id": "Q065",
        "category": "multi_hop",
        "volume": "Volume 4 & 5",
        "query": "What failover mechanisms are triggered by global load balancers when multi-region synchronization experiences clock drift?",
        "expected_keywords": ["load balancer", "failover", "clock drift", "CRDT", "canary"],
        "search_terms": ["NET-GLB", "HA-A2A"]
    },
    {
        "id": "Q066",
        "category": "multi_hop",
        "volume": "Volume 4 & 10",
        "query": "How do progressive traffic canary rollouts (5% to 100%) integrate with global load balancer traffic splitting?",
        "expected_keywords": ["canary", "traffic splitting", "5%", "100%", "rollback"],
        "search_terms": ["SRE-REL", "NET-GLB"]
    },
    {
        "id": "Q067",
        "category": "multi_hop",
        "volume": "Volume 7 & 9",
        "query": "How do Great Expectations data quality assertions protect GDPR Article 17 right to erasure workflows?",
        "expected_keywords": ["Great Expectations", "GDPR", "Article 17", "erasure", "quality"],
        "search_terms": ["STR-QUAL", "REG-GDPR"]
    },
    {
        "id": "Q068",
        "category": "multi_hop",
        "volume": "Volume 8 & 8",
        "query": "Compare FlashAttention-2 GPU kernel efficiency with low-bit AWQ weight quantization in high-throughput LLM serving.",
        "expected_keywords": ["FlashAttention-2", "AWQ", "quantization", "vLLM", "inference"],
        "search_terms": ["ML-QUANT", "ML-SERV"]
    },
    {
        "id": "Q069",
        "category": "multi_hop",
        "volume": "Volume 2 & 9",
        "query": "What enterprise IAM policy changes or break-glass access triggers a mandatory Data Protection Impact Assessment DPIA?",
        "expected_keywords": ["DPIA", "GDPR", "IAM", "break-glass", "compliance"],
        "search_terms": ["REG-GDPR", "SEC-RBAC"]
    },
    {
        "id": "Q070",
        "category": "multi_hop",
        "volume": "Volume 5 & 10",
        "query": "How do primary and secondary on-call rotation schedules interface with Incident Commander roles during SEV-1 outages?",
        "expected_keywords": ["on-call", "Incident Commander", "SEV-1", "escalation", "15-minute"],
        "search_terms": ["SRE-CALL", "SRE-SEV"]
    },
    {
        "id": "Q071",
        "category": "multi_hop",
        "volume": "Volume 1 & 10",
        "query": "What role does eBPF datapath tracing play in both Cilium service mesh networking and SRE OpenTelemetry distributed observability?",
        "expected_keywords": ["eBPF", "Cilium", "OpenTelemetry", "tracing", "observability"],
        "search_terms": ["K8S-NET", "SRE-OBS"]
    },
    {
        "id": "Q072",
        "category": "multi_hop",
        "volume": "Volume 5 & 6",
        "query": "How do preemptible spot instances offering 70% discounts affect SLA uptime calculations and monthly error budgets?",
        "expected_keywords": ["70%", "spot instance", "SLA", "error budget", "preemptible"],
        "search_terms": ["FIN-COMP", "HA-SLA"]
    },
    {
        "id": "Q073",
        "category": "multi_hop",
        "volume": "Volume 3 & 8",
        "query": "How do vector search HNSW graphs optimize similarity search compared to LSM-tree SSTable indexing?",
        "expected_keywords": ["HNSW", "vector", "LSM-tree", "SSTables", "indexing"],
        "search_terms": ["ML-VEC", "DB-ENG"]
    },
    {
        "id": "Q074",
        "category": "multi_hop",
        "volume": "Volume 7 & 10",
        "query": "How does Dead Letter Queue DLQ routing in stream processing trigger automated on-call paging during pipeline failures?",
        "expected_keywords": ["DLQ", "Dead Letter Queue", "on-call", "paging", "streaming"],
        "search_terms": ["STR-QUAL", "SRE-CALL"]
    },
    {
        "id": "Q075",
        "category": "multi_hop",
        "volume": "Volume 2 & 9",
        "query": "What cross-account delegation controls and CMEK key rotation safeguard payment cardholder data under PCI-DSS v4.0?",
        "expected_keywords": ["CMEK", "PCI-DSS", "tokenization", "cardholder", "key rotation"],
        "search_terms": ["SEC-KMS", "REG-PCI"]
    },

    # =========================================================================
    # Category C: 15 Out-of-Domain Negative Queries (Testing Zero Hallucination)
    # =========================================================================
    {
        "id": "Q076",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What quantum teleportation key distribution protocol is specified in Volume 11?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q077",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What is the corporate reimbursement policy for executive private aircraft travel?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q078",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "How many Ethereum validators does the enterprise platform operate for proof-of-stake rewards?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q079",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What is the standard roasting recipe for enterprise cafeteria espresso coffee beans?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q080",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "Where are the subterranean nuclear bunker blueprints stored under Volume 12 disaster procedures?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q081",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What is the daily dog walking allowance provided to remote platform site reliability engineers?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q082",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "Which extraterrestrial alien artifact was analyzed during the third quarter security review?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q083",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What cryptocurrency tokens does the enterprise billing system accept for invoice settlement?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q084",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What is the exact speed of sound measured inside the datacenter liquid cooling subsystem pipes?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q085",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "How many solid gold bullion bars are kept in reserve to back the SLA credit guarantee fund?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q086",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What time does the company rooftop swimming pool open for staff on national holidays?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q087",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What astrological zodiac sign requirement is mandated for senior platform architect candidates?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q088",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "Which secret medieval society manages the enterprise root DNS certificate authority private keys?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q089",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "What is the formal business attire dress code policy enforced for virtual Kubernetes pods?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },
    {
        "id": "Q090",
        "category": "negative",
        "volume": "Out-of-Domain",
        "query": "How many miles per gallon of gasoline does the distributed database engine achieve on highway transport?",
        "expected_keywords": ["no mention", "not contain", "does not contain", "no information"],
        "search_term": None
    },

    # =========================================================================
    # Category D: 10 Numerical / Tabular Queries (Testing Quantitative Reasoning)
    # =========================================================================
    {
        "id": "Q091",
        "category": "numerical",
        "volume": "Volume 6",
        "query": "Based on Section 6.1 and 6.2 pricing, what is the compute cost for 2,500 vCPU-hours at $0.048 per vCPU-hour?",
        "expected_keywords": ["120", "$120", "0.048", "2,500", "compute"],
        "search_term": "FIN-COMP"
    },
    {
        "id": "Q092",
        "category": "numerical",
        "volume": "Volume 6",
        "query": "Under Section 6.4, what percentage discount applies to Tier 2 storage (10-50TB) versus Tier 3 storage (50-250TB)?",
        "expected_keywords": ["12%", "22%", "Tier 2", "Tier 3", "discount"],
        "search_term": "FIN-VOL"
    },
    {
        "id": "Q093",
        "category": "numerical",
        "volume": "Volume 6",
        "query": "What is the monthly cost for 10,000 GB of Hot tier storage at $0.021 per GB-month compared to Cold archive storage at $0.004?",
        "expected_keywords": ["$210", "$40", "0.021", "0.004", "storage"],
        "search_term": "FIN-STOR"
    },
    {
        "id": "Q094",
        "category": "numerical",
        "volume": "Volume 1",
        "query": "Based on Table 1.1 through 1.5, what is the maximum concurrency limit and memory quota in MB for Section 1.5?",
        "expected_keywords": ["300", "150", "1024", "2048", "quota"],
        "search_term": "K8S-ISO"
    },
    {
        "id": "Q095",
        "category": "numerical",
        "volume": "Volume 6",
        "query": "Under Section 6.3 SLA policies, what is the invoice credit granted on a $100,000 bill if system availability drops below 99.0%?",
        "expected_keywords": ["25%", "$25,000", "credit", "99.0%"],
        "search_term": "FIN-CRED"
    },
    {
        "id": "Q096",
        "category": "numerical",
        "volume": "Volume 10",
        "query": "Compare the response SLA for SEV-1 incidents (15 minutes) with the response SLA for SEV-2 incidents (30 minutes).",
        "expected_keywords": ["15", "30", "SEV-1", "SEV-2", "minutes"],
        "search_term": "SRE-SEV"
    },
    {
        "id": "Q097",
        "category": "numerical",
        "volume": "Volume 6",
        "query": "What is the cost of 500 GB internet outbound egress at $0.08 per GB plus 1,000 GB cross-region data transfer at $0.02 per GB?",
        "expected_keywords": ["$40", "$20", "$60", "0.08", "0.02"],
        "search_term": "FIN-STOR"
    },
    {
        "id": "Q098",
        "category": "numerical",
        "volume": "Volume 6",
        "query": "How much discount does preemptible spot instance computing provide over standard capacity (70% discount)?",
        "expected_keywords": ["70%", "discount", "spot", "preemptible", "Standard"],
        "search_term": "FIN-COMP"
    },
    {
        "id": "Q099",
        "category": "numerical",
        "volume": "Volume 9",
        "query": "Compare the GDPR Article 17 erasure statutory deadline of 30 days with the HIPAA audit trail retention period of 6 years.",
        "expected_keywords": ["30 days", "6 years", "GDPR", "HIPAA", "retention"],
        "search_term": "REG-GDPR"
    },
    {
        "id": "Q100",
        "category": "numerical",
        "volume": "Volume 10",
        "query": "What are the automated budget notification percentage thresholds under Section 6.5 FinOps governance?",
        "expected_keywords": ["75%", "90%", "100%", "budget", "thresholds"],
        "search_term": "FIN-TAG"
    }
]

def build_golden_dataset():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    print("Connecting to ChromaDB to map ground-truth chunk IDs...")

    client = chromadb.PersistentClient(path="./data/chroma")
    coll = client.get_collection("documents")
    all_chunks = coll.get(where={"source": "data/enterprise_handbook_500_pages.txt"})

    total_chunks = len(all_chunks["ids"])
    print(f"Loaded {total_chunks} indexed enterprise chunks.")

    queries = []

    for spec in QUERY_SPECS:
        relevant_docs = []

        if spec["category"] == "negative":
            relevant_docs = []

        elif spec.get("search_terms"):
            # Multi-hop: match any chunk containing search terms
            for s_term in spec["search_terms"]:
                for cid, doc in zip(all_chunks["ids"], all_chunks["documents"]):
                    if s_term in doc and cid not in relevant_docs:
                        relevant_docs.append(cid)

        elif spec.get("search_term"):
            s_term = spec["search_term"]
            for cid, doc in zip(all_chunks["ids"], all_chunks["documents"]):
                if s_term in doc:
                    relevant_docs.append(cid)

        entry = {
            "id": spec["id"],
            "category": spec["category"],
            "volume": spec["volume"],
            "query": spec["query"],
            "expected_keywords": spec["expected_keywords"],
            "relevant_docs": relevant_docs
        }
        queries.append(entry)

    dataset = {
        "metadata": {
            "total_queries": len(queries),
            "breakdown": {
                "single_hop": 50,
                "multi_hop": 25,
                "negative": 15,
                "numerical": 10
            },
            "corpus": "data/enterprise_handbook_500_pages.txt",
            "total_indexed_chunks": total_chunks
        },
        "queries": queries
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Golden dataset created successfully at: {OUTPUT_FILE}")
    print(f"Total queries: {len(queries)}")

if __name__ == "__main__":
    build_golden_dataset()
