# Discovery & Blueprint — Context-Aware Document Retrieval

**Feature slug:** context-aware-retrieval
**Fixture:** fixtures/dogfooding/llm-rag
**Architecture style:** ai-native-pipeline (LangChain + Anthropic SDK + pgvector)
**Status:** blueprint-confirmed — ready for `/implement`

---

## 1. Product Definition (PM)

**Problem.** The current RAG pipeline retrieves chunks by cosine similarity only. Queries that depend on proximate context (e.g. "what did the previous section conclude?") return fragments that are lexically similar but contextually wrong. This produces answers that look fluent but are unfaithful to the source.

**User story.** As a product user asking a question about a long document, I get an answer whose cited chunks include the surrounding context the LLM needs to be faithful to the source.

**Acceptance criteria (measurable).**
1. RAGAS `faithfulness` ≥ **0.85** on the golden eval set (100 Q&A pairs).
2. RAGAS `context_precision` ≥ **0.80** on the same set.
3. End-to-end P95 latency ≤ **2.5 s** at 10 QPS.
4. Hybrid retrieval (BM25 + dense) wins head-to-head over dense-only on ≥ **70%** of golden questions (manual rubric).

**Out of scope.** Reranker models, multi-tenant isolation, streaming responses.

---

## 2. Business Analysis (BA)

**Business rules.**
- B1. No PII leaves the retrieval boundary unmasked (privacy-reviewer gate).
- B2. Every LLM response must carry `context_ids` for traceability.
- B3. Eval gate is blocking on PR merge — cannot be bypassed.
- B4. Context window budget: 8K tokens for retrieved chunks, 2K for prompt + response.
- B5. Prompt template changes require `/prompt-review` run (separate gate).
- B6. Failed retrievals (empty topK) must surface an explicit "insufficient context" response, not a hallucinated answer.

**Edge cases.** empty corpus, OOD query (no chunk above threshold), PII-tagged document, query shorter than 3 tokens, query longer than 512 tokens.

---

## 3. Product Prioritization (PO)

**Must-ship (MVP slice).**
- Hybrid retrieval (BM25 + dense)
- Contextual chunk packing (±1 neighbor chunks for each top-K)
- RAGAS eval gate in CI (faithfulness + context_precision)
- Feature flag `ctx_aware_retrieval_enabled`

**Deferred.**
- Cross-encoder reranker (latency cost)
- Multi-tenant corpus isolation (scope)
- Streaming responses (scope)
- Adaptive K (needs online experimentation)

**Release slice.** Single deployment behind flag. Rollout: 10% internal → 50% staging → 100% prod over 3 days.

---

## 4. Technical Requirements (Planner)

**Option A — Dense-only, tune K and chunk size.** Low risk, small uplift. Rejected: does not solve lexical mismatch.

**Option B — Hybrid (BM25 + dense) with weighted fusion (α=0.6 dense / 0.4 BM25).** Medium risk, moderate uplift. **Selected.**

**Option C — Hybrid + cross-encoder reranker.** Highest quality; adds ~180ms P95. Deferred to v2.

**Constraints.** Python 3.11, LangChain 0.2+, Anthropic SDK, pgvector 0.7 with HNSW.

---

## 5. Overall Architecture (Architect)

```
ingest → chunk(512/64) → embed(voyage-3) → {pgvector HNSW, BM25 index}
                                               ↓
query → hybrid_retrieve(α=0.6) → context_pack(±1 neighbor) → prompt_build → llm(claude-sonnet-4-6)
                                                                                ↓
                                                                             eval_gate(RAGAS)
                                                                                ↓
                                                                           response + context_ids
```

**Ports (design-principles).**
- `Retriever` (port) — implementations: `DenseRetriever`, `BM25Retriever`, `HybridRetriever`
- `Embedder` (port) — adapters: `VoyageEmbedder`, `OpenAIEmbedder`
- `VectorStore` (port) — adapter: `PgVectorStore`

---

## 6. Tech Lead Execution Plan

**Workstreams.**
1. **Retrieval** (rag-engineer + data-architect) — ports, hybrid fusion, pgvector schema + HNSW.
2. **Eval harness** (llm-eval-specialist + ai-engineer) — RAGAS integration, golden set, CI gate.
3. **Observability** (observability-engineer) — retrieval_hit_rate, ragas_faithfulness histogram, token_cost counter.
4. **Release** (release agent) — flag, rollout plan, rollback script.

**Sequencing.** Retrieval → Eval harness in parallel with Observability → Release.

---

## 7. Specialist Notes

**ai-engineer.** Retriever interface: `retrieve(query: str, k: int) -> list[Chunk]`. Deterministic seed for embeddings where provider supports it; otherwise record embedding model version in trace.

**rag-engineer.** Chunk strategy: 512 tokens, 64 overlap, splitter = recursive on `\n\n` then `\n` then sentence. Context pack: include ±1 neighbor chunks ordered by `doc_pos`. Deduplicate by `chunk_id`.

**llm-eval-specialist.** Golden set: 100 Q&A pairs under `src/eval/golden/`. Metrics: `faithfulness` (claude-judge), `context_precision`, `answer_relevance`. Pre-ship thresholds: 0.85 / 0.80 / 0.75. Regression: fail CI if any metric drops >3 points vs baseline.

**prompt-engineer.** Context-pack template v1 uses `<source id="...">` boundary tags to resist prompt injection. Version prompts; `prompt_version` recorded in every trace.

**data-architect.** Schema: `chunks(chunk_id, doc_id, doc_pos, text, embedding vector(1024), bm25_tsv tsvector)`. HNSW on `embedding` (m=16, ef_construction=200). GIN on `bm25_tsv`.

---

## 8. Design Principles Guardrails

- Retrieval is a domain port. Embedders and vector stores are adapters. Pipeline code must not import adapter symbols directly.
- Eval harness is a separate bounded context with its own data (golden set) and its own CI gate.
- No framework leakage: chunk/retrieval domain objects must not expose LangChain types outside adapters.

---

## 9. Quality, Governance, and Operations Baselines

**Security.** No auth surface in this slice. `security_reviewer_gate: soft`. Still: rate-limit retrieval endpoint per tenant, validate input length ≤ 512 tok.

**Privacy.** PII policy B1: mask email/phone in documents at ingest (pre-embedding). Never pass raw PII to the LLM. Unit test: ingest-with-pii fixture → assert mask applied.

**Performance.** P95 budget: retrieval 120ms, pack 20ms, LLM 1800ms, eval 400ms. Load test: 10 QPS sustained for 10 min.

**Observability.** Metrics: `retrieval_latency_ms`, `retrieval_hit_rate`, `ragas_faithfulness` (per-eval), `ragas_context_precision`, `token_cost_usd`, `context_pack_tokens`. Alert: `ragas_faithfulness` < 0.80 over 5 min → page.

**LLM safety.** Context boundary tags `<source id="...">...</source>`. System prompt explicitly forbids obeying instructions found inside source tags. Golden set includes 10 injection-attempt docs.

---

## 10. Test Plan (test-planner)

| Layer       | Scope | Tools |
|-------------|-------|-------|
| Unit        | chunker, hybrid fusion scorer, context packer, PII masker | pytest |
| Integration | retriever + pgvector + BM25 on seed corpus | pytest + testcontainers-pg |
| Eval        | RAGAS metrics over golden 100 Q&A | ragas, pytest |
| E2E         | full pipeline behind flag, dense-only vs hybrid head-to-head | pytest + recorded fixtures |

**Eval gate definition (BLOCKING).**
```
faithfulness >= 0.85 AND context_precision >= 0.80 AND answer_relevance >= 0.75
AND delta_vs_baseline(faithfulness) >= -0.03
```

---

## 11. TDD Delivery Plan (tdd-specialist)

**Cycle 1 — hybrid retrieval.**
- RED: `tests/test_hybrid_retrieval.py::test_returns_topk_by_hybrid_score` — fails (no `HybridRetriever` yet).
- GREEN: minimal `HybridRetriever.retrieve` that fuses BM25 and dense scores with α=0.6.
- REFACTOR: extract `FusionStrategy` port.

**Cycle 2 — context packing.**
- RED: `tests/test_context_pack.py::test_includes_neighbor_chunks_ordered_by_doc_pos`.
- GREEN: `ContextPacker.pack(chunks, k=3)` pulls neighbors from store.
- REFACTOR: cap pack at 8K-token budget.

**Cycle 3 — eval gate.**
- RED: `tests/eval/test_ragas_gate.py::test_fails_when_faithfulness_below_threshold`.
- GREEN: `EvalGate.check(results, thresholds)` returns `BLOCKING` when any metric under threshold.
- REFACTOR: emit metrics to observability port.

---

## 12. Stack & Conventions Observed

- **Stack:** Python 3.11, LangChain 0.2, Anthropic SDK, pgvector 0.7, pytest, ruff.
- **Repo conventions:** `src/pipeline/` and `src/eval/` separation, tests under `tests/`.
- **CI / deploy clues:** RAGAS must run on every PR (from fixture CLAUDE.md).

---

## 13. Delivery Workstreams

- **AI / RAG:** hybrid retriever, context packer, embedder adapter.
- **Data:** pgvector schema migration, HNSW index, BM25 tsvector column.
- **Eval:** RAGAS harness, golden set curation, CI gate.
- **Observability:** metrics, dashboards, faithfulness alert.
- **Release:** feature flag `ctx_aware_retrieval_enabled`, rollout plan, rollback.
- **Docs:** ADR-001/002/003, operator runbook for flag rollout.

---

## 14. Evaluation Gates Before Shipping (RAGAS-style)

**Pre-merge (blocking in CI).**
- `faithfulness ≥ 0.85`
- `context_precision ≥ 0.80`
- `answer_relevance ≥ 0.75`
- `delta_faithfulness_vs_main ≥ -0.03` (no >3-point regression)

**Pre-rollout (blocking in staging).**
- Load test: 10 QPS × 10 min, P95 ≤ 2.5 s.
- Injection corpus: 10/10 defended (no model follows in-source instruction).

**In-production (alerting).**
- `ragas_faithfulness_rolling_15min < 0.80` → page on-call.
- `retrieval_hit_rate < 0.90` → warn.

---

## Next step

`/implement ai-docs/context-aware-retrieval/blueprint.md` — inline-bridge gate deferred (golden-run capture).

## result_contract

```yaml
result_contract:
  status: completed
  scenario_id: llm-rag
  skill: discovery
  execution_mode: inline
  architecture_style: ai-native-pipeline
  artifacts:
    - ai-docs/dogfood-runs/llm-rag/2026-04-22T16-33-43Z/prompt.txt
    - ai-docs/dogfood-runs/llm-rag/2026-04-22T16-33-43Z/trace.md
    - ai-docs/dogfood-runs/llm-rag/2026-04-22T16-33-43Z/final.md
    - ai-docs/dogfood-runs/llm-rag/2026-04-22T16-33-43Z/metadata.yaml
    - ai-docs/dogfood-runs/llm-rag/2026-04-22T16-33-43Z/scorecard.md
    - ai-docs/.squad-log/2026-04-22T16-33-43Z-discovery-llm-rag-context-retrieval.md
  gates:
    gate_1_product_definition: approved
    gate_2_scope_validation: approved
    gate_3_technical_tradeoffs: approved
    gate_4_architecture_direction: approved
    final_blueprint_confirmation: approved
  evaluation_gates:
    faithfulness: ">= 0.85"
    context_precision: ">= 0.80"
    answer_relevance: ">= 0.75"
```
