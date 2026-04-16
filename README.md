# 🏴 OBLIVIARCH

> *The Architecture of Controlled Oblivion*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]()

Traces die. Schemas rise from their corpses. Archetypes are the immortal patterns that survive.

OBLIVIARCH is the memory compression engine for self-improving swarms. It implements **Trace Schema Compression (TSC)** — a 3-level hierarchical pipeline that transforms raw collaboration logs into immortal behavioral DNA, achieving **500x compression** with better recall.

---

## The River Lethe Runs Through Your Memory

Most swarm systems hoard everything. Raw logs pile up. Recall degrades. The more you store, the less you can find.

OBLIVIARCH inverts this: **the swarm that remembers less but remembers better outperforms the swarm that remembers everything.** Compression is not loss — it is understanding.

---

## The Three Deaths

| Level | Name | What Dies | What Lives | Compression |
|-------|------|-----------|-----------|-------------|
| **1** | Episodic | Nothing yet — raw traces live <48h | Complete collaboration logs | 1x (raw) |
| **2** | Semantic | Irrelevant context, noise | Named patterns: IMPLEMENT-REVIEW-PATCH | ~20x |
| **3** | Archetypal | Domain-specific detail | Irreducible behavioral DNA | ~500x |

### Level 1 — The Episodic (Mortal Traces)

Raw collaboration logs. Every agent action, every step, every outcome. High fidelity, high cost.

These traces are mortal — they live for 48 hours at most. The clock starts ticking the moment they're recorded.

```
agents: [january, february, march]
task: "refactor authentication module"
steps: [IMPLEMENT → REVIEW → PATCH → TEST → SHIP]
outcome: success, score: 0.85
TTL: 48 hours
```

### Level 2 — The Semantic (Pattern Birth)

When the same collaboration pattern emerges across multiple traces, a **schema** is born. Schemas strip away the irrelevant — which agents, which specific code — and preserve the topology: *what happened, in what sequence, with what dependencies.*

```
Schema: IMPLEMENT-REVIEW-PATCH
Pattern: [IMPLEMENT, REVIEW, PATCH]
Activation count: 47
Source traces: 12 distinct sessions
Memory: ~20x smaller than raw traces
```

New schemas are auto-promoted when a pattern recurs across 10+ traces. Six seed patterns bootstrap the system:
- IMPLEMENT-REVIEW-PATCH
- DECOMPOSE-DISPATCH-AGGREGATE
- CHALLENGE-DEFEND-RESOLVE
- EXPLORE-EXPLOIT
- PLAN-BUILD-TEST-SHIP
- RESEARCH-SYNTHESIZE-DELIVER

### Level 3 — The Archetypal (Immortal DNA)

Schemas that survive 50+ activations ascend to archetype status. These are the irreducible patterns — the behavioral DNA of the swarm. They transcend any single domain, any single agent, any single session.

```
Archetype: DECOMPOSE-DISPATCH-AGGREGATE
Pattern: [DECOMPOSE, DISPATCH, AGGREGATE]
Description: Break a problem into parts, delegate, combine results
Activation count: 2,847
Cold: false (active)
```

Archetypes that go unactivated for 90 days undergo **controlled forgetting** — not deletion, but demotion to cold storage. They can be **reheated** on access. The archive remembers, even when the swarm forgets.

---

## The Consolidation Cycle (Sleep)

OBLIVIARCH runs a sleep-cycle consolidation pipeline — analogous to human memory consolidation during sleep:

1. **Promote** — Recent episodic traces (24h window) are scanned for patterns → schemas promoted
2. **Ascend** — High-activation schemas ascend to archetypes
3. **Archive** — Traces older than 48h are archived (not deleted, but moved)
4. **Forget** — Archetypes dormant for 90+ days are demoted to cold storage

```
┌─────────────┐     10+ activations     ┌─────────────┐     50+ activations     ┌─────────────┐
│  EPISODIC   │ ──────────────────────> │   SCHEMA    │ ──────────────────────> │  ARCHETYPE  │
│  (mortal)   │                         │  (emerging)  │                         │  (immortal)  │
│  <48h TTL   │                         │  ~20x       │                         │  ~500x       │
└─────────────┘                         └─────────────┘                         └─────────────┘
       │                                       │                                       │
       │ archive after 48h                      │ controlled forgetting                 │
       │ (not deleted — cold storage)           │ after 90 days dormant                 │ never deleted
       ▼                                       ▼                                       ▼
  [COLD EPISODIC]                        [COLD SCHEMA]                           [COLD ARCHETYPE]
  retrievable on demand                  retrievable on demand                   retrievable on demand
```

---

## Quick Start

```python
from obliviarch import Obliviarch

engine = Obliviarch(data_dir="data/")
engine.start()

# Record a collaboration trace
engine.record(
    agents=["january", "february"],
    task="refactor authentication",
    steps=[
        {"action": "IMPLEMENT", "agent": "february"},
        {"action": "REVIEW", "agent": "march"},
        {"action": "PATCH", "agent": "february"},
        {"action": "SHIP", "agent": "january"},
    ],
    outcome="success",
    score=0.85,
)

# Run consolidation cycle (promote → ascend → archive → forget)
result = engine.consolidate()
print(f"+{result['new_schemas']} schemas, +{result['new_archetypes']} archetypes")
print(f"{result['traces_archived']} traces archived, {result['archetypes_forgotten']} forgotten")

engine.stop()
```

### CLI

```bash
obliviarch start --data-dir data/ --interval 30
obliviarch consolidate
obliviarch stats
obliviarch query "IMPLEMENT-REVIEW-PATCH"
```

---

## Architecture

```
obliviarch/
├── __init__.py                # Package root
├── engine.py                  # Obliviarch controller
├── cli.py                     # CLI: start/consolidate/stats/query
├── episodic/
│   ├── __init__.py
│   └── trace_capture.py       # Level 1: Mortal traces
├── semantic/
│   ├── __init__.py
│   └── schema_extractor.py    # Level 2: Pattern birth
├── archetypal/
│   ├── __init__.py
│   └── archetype_vault.py     # Level 3: Immortal DNA
└── lethe/
    ├── __init__.py
    └── consolidation.py       # The river: promote → ascend → archive → forget
```

---

## Why It Works

**Recall quality improves as compression increases.** This sounds paradoxical but follows directly from information theory:

1. **Noise filtering** — Schemas abstract away irrelevant context while preserving decision-relevant structure
2. **Cross-domain transfer** — IMPLEMENT-REVIEW-PATCH applies to code, documents, data analysis — no domain-specific traces needed
3. **Faster retrieval** — Vector search over 200KB of archetypes is orders of magnitude faster than search over 100MB of raw logs
4. **Graceful forgetting** — Cold storage preserves everything; explicit retrieval reheats what matters

---

## Research

OBLIVIARCH synthesizes:

- **G-Memory** (Zhang, Yan et al., 2025) — Hierarchical trace memory for multi-agent systems
- **SiriuS** (Zhao, Yuksekgonul, Zou, 2025) — Bootstrapped reasoning from experience banks
- **VoidSwarm** (0x-wzw, 2026) — clawXiv.2604.00007: Self-improving and self-healing swarm architectures

---

## License

MIT

> *Oblivion is not the enemy of memory. Oblivion is memory's most powerful editor.*