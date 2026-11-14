#!/usr/bin/env python3
"""Generate a synthetic 500-page realistic enterprise technical handbook."""

from pathlib import Path

OUTPUT_FILE = Path("data/enterprise_handbook_500_pages.txt")

TOPICS = [
    {
        "volume": "Volume 1: Cloud Infrastructure & Kubernetes Architecture",
        "code": "INFRA",
        "sections": [
            ("Kubernetes Control Plane Dynamics", "K8S-CTRL", "etcd consistency models, API server rate limiting, leader election with leases, controller manager synchronization loops, scheduler scoring algorithms"),
            ("Container Network Interface and Service Mesh", "K8S-NET", "eBPF datapaths, Cilium Hubble observability, mTLS sidecar proxies, Envoy connection pooling, IPAM subnet allocation"),
            ("Persistent Storage Subsystems and CSI Drivers", "K8S-STOR", "dynamic provisioning, block vs filesystem mounts, volume snapshot controllers, read-write-many NFS protocols, ephemeral inline volumes"),
            ("Autoscaling Strategies and Workload Profiling", "K8S-AUTO", "horizontal pod autoscaler HPA metrics, KEDA event-driven triggers, vertical pod autoscaler VPA recommendations, cluster autoscaler node provisioning"),
            ("Cluster Multi-Tenancy and Namespace Isolation", "K8S-ISO", "NetworkPolicies, Pod Security Standards PSS, Admission Webhooks, ResourceQuotas, LimitRanges, hierarchical namespaces HNC"),
        ]
    },
    {
        "volume": "Volume 2: Enterprise Security, Zero-Trust Architecture & IAM",
        "code": "SEC",
        "sections": [
            ("Identity Federation and Token Cryptography", "SEC-IAM", "OAuth 2.0 authorization code flow with PKCE, OpenID Connect discovery, JWT asymmetric signatures using RS256, token revocation lists"),
            ("Role-Based Access Control and Attribute-Based Policies", "SEC-RBAC", "least-privilege permission grants, conditional IAM policies, dynamic role assumption, time-bound break-glass access, cross-account delegation"),
            ("Key Management Service and Envelope Cryptography", "SEC-KMS", "hardware security module HSM tiering, customer managed encryption keys CMEK, symmetric 256-bit AES-GCM data key rotation, envelope decryption"),
            ("Zero-Trust Network Access and Perimeter Defense", "SEC-ZTNA", "context-aware access proxies, device posture validation, software-defined perimeters SDP, mutual TLS mTLS cipher negotiation, microsegmentation"),
            ("Vulnerability Scanning and Supply Chain Security", "SEC-SUPP", "software bill of materials SBOM generation, cryptographic artifact signing with Cosign, base image provenance SLSA Level 3, CVE severity scoring"),
        ]
    },
    {
        "volume": "Volume 3: Distributed Database Internals & Storage Engines",
        "code": "DATA",
        "sections": [
            ("Consensus Protocols and Quorum Architectures", "DB-CONS", "Raft protocol state transitions, log replication, heartbeat timeouts, Paxos phase-1/phase-2 ballot numbers, split-brain mitigation"),
            ("Storage Engines and Index Structures", "DB-ENG", "LSM-tree memtables and SSTables, compaction algorithms (leveled vs size-tiered), B+ tree page splitting, write-ahead logging WAL durability"),
            ("Distributed Transactions and Concurrency Control", "DB-TXN", "two-phase commit 2PC, multi-version concurrency control MVCC, snapshot isolation, serializable ACID anomalies, distributed deadlock detection"),
            ("Data Partitioning and Consistent Hashing", "DB-PART", "virtual node distribution, range-based partitioning, hash ring rebalancing, replication factor RF=3 write quorums, anti-entropy Merkle trees"),
            ("Cache Coherency and Query Optimization", "DB-OPT", "write-through vs write-behind caching, Redis cluster slot allocation, cost-based optimizer statistics, join pushdown, columnar projection pushdown"),
        ]
    },
    {
        "volume": "Volume 4: Network Protocols, Edge CDN & Routing",
        "code": "NET",
        "sections": [
            ("BGP Anycast Routing and Traffic Ingestion", "NET-BGP", "autonomous system AS path selection, BGP community tagging, Anycast route flap damping, latency-based GeoDNS routing, ECMP load balancing"),
            ("HTTP/3 and Modern Transport Layers", "NET-H3", "QUIC protocol frame structure, UDP zero-RTT connection resumption, head-of-line blocking avoidance, connection migration across IP changes"),
            ("Edge Caching, Cache Invalidation and Edge Compute", "NET-CDN", "stale-while-revalidate semantics, surrogate keys for targeted cache purging, edge server worker runtimes, byte-range request streaming"),
            ("DDoS Mitigation and Rate Limiting Algorithms", "NET-DDOS", "token bucket and leaky bucket algorithms, SYN cookie handshakes, upstream scrubbing centers, volumetric attack scrubbing, TLS fingerprinting"),
            ("Global Load Balancing and Traffic Splitting", "NET-GLB", "weighted round-robin, least connections algorithm, active health probing, canary traffic shifting, cross-datacenter failover"),
        ]
    },
    {
        "volume": "Volume 5: Disaster Recovery, High Availability & SLAs",
        "code": "HA",
        "sections": [
            ("Recovery Objectives and Business Continuity", "HA-RTO", "Recovery Time Objective RTO thresholds, Recovery Point Objective RPO limits, cold vs warm vs hot standby failover protocols, DR tier classification"),
            ("Active-Active Multi-Region Synchronization", "HA-A2A", "bi-directional asynchronous data replication, conflict-free replicated data types CRDT, cross-region clock drift management, split-brain resolution"),
            ("Chaos Engineering and Resilience Testing", "HA-CHAOS", "fault injection experiments, network latency simulation, kill-pod automation, cascading dependency failure prevention, bulkhead isolation patterns"),
            ("Service Level Agreements and Error Budgets", "HA-SLA", "four nines 99.99% availability calculations, monthly error budget burn rates, composite SLA degradation rules, downtime refund credits"),
            ("Backup Strategies, Retention and Immutability", "HA-BAK", "WORM object storage immutability, periodic point-in-time recovery PITR, encrypted air-gapped snapshots, automated restore drill validation"),
        ]
    },
    {
        "volume": "Volume 6: Enterprise Financial Policies, Billing & Pricing",
        "code": "FIN",
        "sections": [
            ("Compute and Memory Consumption Tiers", "FIN-COMP", "Standard tier compute unit cost ($0.048 per vCPU-hour), High-Memory tier ($0.092 per GB-hour), preemptible spot instance 70% discounts, reserved capacity commitments"),
            ("Storage and Data Egress Fee Structures", "FIN-STOR", "Hot tier storage ($0.021 per GB-month), Cold archive storage ($0.004 per GB-month), cross-region data transfer ($0.02 per GB), internet outbound egress ($0.08 per GB)"),
            ("Enterprise SLA Credits and Penalties", "FIN-CRED", "uptime below 99.9% grants 10% invoice credit, uptime below 99.0% grants 25% invoice credit, uptime below 95.0% grants 100% full invoice credit"),
            ("Volume Licensing and Tiered Thresholds", "FIN-VOL", "Tier 1 (1-10TB): standard price; Tier 2 (10-50TB): 12% discount; Tier 3 (50-250TB): 22% discount; Tier 4 (250TB+): negotiated custom contract"),
            ("Cost Allocation Tags and FinOps Governance", "FIN-TAG", "mandatory department cost-center tagging, idle resource reclamation policies, automated budget alerts at 75%, 90%, and 100% thresholds"),
        ]
    },
    {
        "volume": "Volume 7: Data Engineering & Real-Time Streaming",
        "code": "STREAM",
        "sections": [
            ("Distributed Event Streaming Architecture", "STR-KAFKA", "partition reassignment, commit log retention segments, consumer group rebalancing protocols, exactly-once processing semantics EOS with idempotent producers"),
            ("Stateful Stream Processing Engines", "STR-FLINK", "RocksDB state backend checkpointing, distributed snapshot algorithm Chandy-Lamport, event time vs processing time, watermark delay thresholds"),
            ("Lakehouse Storage Formats and ACID Transactions", "STR-LAKE", "Parquet columnar encoding with dictionary compression, metadata log versioning, time-travel queries, write-audit-publish patterns"),
            ("Data Quality Validation and Schema Evolution", "STR-QUAL", "backward and forward Avro schema compatibility, Dead Letter Queue DLQ routing, Great Expectations assertions, automated anomaly alerts"),
            ("Batch ETL Orchestration and DAG Execution", "STR-DAG", "dynamic task generation, backfill concurrency controls, idempotent pipeline restarts, lineage tracking, metadata catalogs"),
        ]
    },
    {
        "volume": "Volume 8: Machine Learning Infrastructure & LLM Serving",
        "code": "ML",
        "sections": [
            ("High-Throughput LLM Serving Architectures", "ML-SERV", "vLLM PagedAttention virtual memory allocation, continuous batching iteration scheduling, prefix caching for multi-turn chats, KV-cache quantization"),
            ("Distributed Model Parallelism Techniques", "ML-PARA", "Megatron-style tensor parallelism across GPU ranks, ZeRO stage-3 parameter sharding, pipeline parallelism micro-batching, NCCL all-reduce collectives"),
            ("Low-Bit Quantization and Kernel Optimization", "ML-QUANT", "AWQ activation-aware weight quantization, GPTQ second-order Taylor expansion, FP8 mixed-precision matrix multiplication, FlashAttention-2 GPU kernels"),
            ("Vector Search Indexing and Approximate Nearest Neighbors", "ML-VEC", "Hierarchical Navigable Small World HNSW graphs, Inverted File Flat IVF-FLAT indexes, product quantization PQ compression, cosine vs dot-product similarity metrics"),
            ("Model Monitoring, Drift and Alignment", "ML-EVAL", "embedding drift detection using Wasserstein distance, token latency p95/p99 benchmarking, safety guardrail classifiers, RLHF reward modeling"),
        ]
    },
    {
        "volume": "Volume 9: Legal, Compliance & Regulatory Standards",
        "code": "LEGAL",
        "sections": [
            ("GDPR Compliance and Data Privacy Safeguards", "REG-GDPR", "Article 17 right to erasure (data deletion within 30 days), Article 20 data portability, Data Protection Impact Assessment DPIA triggers, cross-border transfer Standard Contractual Clauses SCCs"),
            ("Healthcare Compliance under HIPAA Security Rules", "REG-HIPAA", "ePHI encryption in transit and at rest, Business Associate Agreement BAA mandates, minimum necessary standard, 6-year audit trail retention"),
            ("SOC 2 Type II Trust Services Criteria", "REG-SOC2", "Security, Availability, Processing Integrity, Confidentiality, and Privacy criteria; continuous evidence collection, external third-party auditor evaluations"),
            ("Payment Card Industry Data Security Standard", "REG-PCI", "PCI-DSS v4.0 requirement 3 cardholder data tokenization, requirement 10 automated audit logging, quarterly external vulnerability ASV scanning"),
            ("Financial Records Retention and Auditing", "REG-SEC17", "SEC Rule 17a-4 non-rewritable non-erasable storage format, 7-year statutory financial retention, automated legal hold freezing"),
        ]
    },
    {
        "volume": "Volume 10: SRE Protocols, Incident Response & Runbooks",
        "code": "SRE",
        "sections": [
            ("Incident Severity Classification Matrix", "SRE-SEV", "SEV-1 (complete outage, 15-minute response SLA), SEV-2 (degraded core workflow, 30-minute SLA), SEV-3 (minor bug, 4-hour SLA), Incident Commander roles"),
            ("On-Call Paging and Escalation Trees", "SRE-CALL", "primary/secondary rotation schedules, automated unacknowledged alert escalation after 5 minutes, follow-the-sun global handover protocols"),
            ("Post-Mortem Analysis and Blameless Culture", "SRE-POST", "5-Whys root cause analysis, timeline construction, preventive action item tracking, publishing blameless post-mortem within 72 hours of resolution"),
            ("Observability Telemetry and Distributed Tracing", "SRE-OBS", "OpenTelemetry span propagation, context injection, Prometheus PromQL alerting rules, Grafana dashboard Golden Signals (latency, traffic, errors, saturation)"),
            ("Production Change Management and Canary Rollouts", "SRE-REL", "progressive traffic shifting (5% -> 25% -> 100%), automated rollback on HTTP 5xx error spikes, blue-green deployment database schema migrations"),
        ]
    }
]

def generate_corpus():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"Generating 500-page enterprise handbook at: {OUTPUT_FILE}")

    # Each page in publishing is ~400 words. 500 pages = 200,000 words.
    # 10 volumes * 5 sections = 50 sections.
    # Each section needs ~4,000 words (10 pages per section * 50 sections = 500 pages).

    total_words = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# ENTERPRISE GLOBAL PLATFORM ARCHITECTURE & OPERATING HANDBOOK\n")
        f.write("### Production Edition | Total Volumes: 10 | Target Scope: 500 Pages\n\n")

        for vol_idx, vol in enumerate(TOPICS, 1):
            f.write(f"\n{'='*80}\n")
            f.write(f"# {vol['volume']}\n")
            f.write(f"{'='*80}\n\n")

            for sec_idx, (sec_title, sec_code, keywords) in enumerate(vol["sections"], 1):
                f.write(f"\n## Section {vol_idx}.{sec_idx}: {sec_title} [REF: {sec_code}-{vol_idx:02d}{sec_idx:02d}]\n\n")
                f.write(f"**Document ID**: DOC-{sec_code}-{vol_idx:02d}{sec_idx:02d}\n")
                f.write("**Classification**: STRICTLY CONFIDENTIAL - ENTERPRISE INTERNAL OPERATING PROCEDURE\n")
                f.write(f"**Core Subject Domain**: {keywords}\n\n")

                # Generate detailed paragraphs totaling ~4,000 words per section
                subtopics = [
                    ("Architectural Overview & Foundational Principles", 8),
                    ("Technical Specifications & Deep-Dive Mechanics", 10),
                    ("Enterprise Governance, Security & Boundary Controls", 8),
                    ("Failure Modes, Edge Cases & Operational Runbooks", 8),
                    ("Quantitative Benchmarks, SLA Thresholds & Metrics", 8),
                ]

                for sub_title, num_paragraphs in subtopics:
                    f.write(f"### {vol_idx}.{sec_idx} Sub-Clause: {sub_title}\n\n")
                    for p_idx in range(1, num_paragraphs + 1):
                        paragraph = (
                            f"Clause {vol_idx}.{sec_idx}.{p_idx} specifies the governing operational framework for "
                            f"{sec_title.lower()} within the global enterprise architecture. Under operational standard "
                            f"{sec_code}-{vol_idx:02d}{p_idx:02d}, all subsystem modules handling {keywords} must enforce strict "
                            f"idempotency, telemetry emission, and failure boundary isolation. When executing under multi-region "
                            f"distributed conditions, the runtime guarantees deterministic synchronization using verified "
                            f"cryptographic handshakes and persistent state ledgers. In benchmark testing under peak load, "
                            f"the system demonstrated p99 processing latency below 12.4 milliseconds while sustaining zero "
                            f"data corruption across all active nodes. Administrators and platform engineers must never bypass "
                            f"the verification gates defined in sub-clause {vol_idx}.{sec_idx}. Failure to adhere to policy "
                            f"{sec_code}-{vol_idx:02d}{p_idx:02d} constitutes an immediate compliance violation subject to "
                            f"automated remediation protocols and escalation to the global technical oversight committee. "
                            f"Furthermore, integration with upstream event buses requires monotonic sequence numbering and "
                            f"explicit lease expiration timers configured to a default maximum threshold of 30,000 milliseconds. "
                            f"Telemetry streams must capture request headers, payload checksums, and distributed trace contexts "
                            f"conforming to OpenTelemetry semantic conventions before emitting records to persistent cold storage.\n\n"
                        )
                        f.write(paragraph)
                        total_words += len(paragraph.split())

                # Add a structured table for numerical / tabular questions
                f.write(f"#### Table {vol_idx}.{sec_idx}: Quantitative Parameter Matrix for {sec_code}\n\n")
                f.write("| Parameter Key | Standard Value | Maximum Threshold | Enforcement Unit | Action on Breach |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- |\n")
                f.write(f"| {sec_code}_TIMEOUT_MS | 30000 | 60000 | Milliseconds | Force Termination |\n")
                f.write(f"| {sec_code}_CONCURRENCY_LIMIT | {vol_idx * 150} | {vol_idx * 300} | Active Sessions | Backpressure Queue |\n")
                f.write(f"| {sec_code}_ERROR_THRESHOLD_PCT | 0.05 | 0.10 | Percentage | Circuit Breaker Open |\n")
                f.write(f"| {sec_code}_MEMORY_QUOTA_MB | {vol_idx * 1024} | {vol_idx * 2048} | Megabytes | Pod Eviction |\n\n")
                total_words += 40

    print(f"Generated successfully! Total words: {total_words:,} (~{total_words / 400:.1f} standard book pages)")

if __name__ == "__main__":
    generate_corpus()

