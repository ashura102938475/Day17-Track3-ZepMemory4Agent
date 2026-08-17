# Day 17 — Multi-Memory Agent

## Benchmark

Student retrieval passed **11/11 practice cases** (100% memory hit rate), with average latency **741.3 ms** and average token reduction **14.19%**. The lowest-hit layer was a tie: short-term, long-term, and episodic all passed their cases; therefore no layer had a lower hit rate. The largest retrieval was E02 with **1,409 tokens**. E07 combines long-term and semantic memory; its required evidence is Minh’s **Python** preference and the shared **Idempotency-Key** payment rule. No-memory passed only 2/11: its high apparent reduction comes from retrieving almost nothing, so it saves tokens by losing evidence rather than by selecting useful context.

Golden evaluation also passed **20/20** for the full **+10 bonus**.

## Reflection

The most important layer here is long-term memory, especially E08: the project-scoped TypeScript/NestJS constraint must override Minh’s general Python preference. This demonstrates that user and project scope plus recency matter more than a plausible generic answer.

Zep Context Block provides managed cross-thread recall and relevance construction, while Redis plus Qdrant gives more control over schemas, filtering, TTLs, cost, and local operation—but requires implementing ingestion, ranking, isolation, and lifecycle yourself. A durable write or heartbeat should require explicit consent, allowed memory types, PII minimization, scoped authorization, provenance, confidence/TTL, and an audit trail; background work must never grant itself write permission.

E08 succeeds because the newer BLUEBIRD-42 constraint is retrieved in the correct user graph and remains scoped to that project. E10 succeeds because compaction preserves the durable deadline marker even after older raw turns are evicted; a fluent summary alone would not be sufficient evidence.

## Evidence

- `reports/benchmark.json` / `.md`: practice metrics and case evidence
- `reports/golden_benchmark.json` / `.md`: 20/20 golden result
- `reports/benchmark_no_memory.json` / `.md`: baseline
- `reports/comparison.md`: memory-enabled comparison
