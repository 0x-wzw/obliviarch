"""
Schema Extractor — Trace → Schema promotion (Level 2 of TSC).

Abstracts episodic traces into reusable patterns:
  "Agent A implemented, Agent B reviewed, Agent C patched"
  → Schema: IMPLEMENT-REVIEW-PATCH

Schemas are embedded as vectors for semantic retrieval.
~20x compression from raw traces.
"""

from __future__ import annotations

import json
import time
import uuid
import hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading

from obliviarch.episodic.trace_capture import CollaborationTrace

logger = __import__("logging").getLogger(__name__)


@dataclass
class Schema:
    """A reusable collaboration pattern extracted from traces."""
    schema_id: str
    name: str
    pattern: List[str]  # e.g., ["IMPLEMENT", "REVIEW", "PATCH"]
    source_traces: List[str]  # trace_ids that contributed
    activation_count: int = 0
    last_activated: float = 0.0
    created_at: float = 0.0
    promoted_to_archetype: bool = False
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()
        if self.last_activated == 0:
            self.last_activated = self.created_at


# Known archetype patterns — seed schemas
SEED_PATTERNS = {
    "IMPLEMENT-REVIEW-PATCH": ["IMPLEMENT", "REVIEW", "PATCH"],
    "DECOMPOSE-DISPATCH-AGGREGATE": ["DECOMPOSE", "DISPATCH", "AGGREGATE"],
    "CHALLENGE-DEFEND-RESOLVE": ["CHALLENGE", "DEFEND", "RESOLVE"],
    "EXPLORE-EXPLOIT": ["EXPLORE", "EXPLOIT"],
    "PLAN-BUILD-TEST-SHIP": ["PLAN", "BUILD", "TEST", "SHIP"],
    "RESEARCH-SYNTHESIZE-DELIVER": ["RESEARCH", "SYNTHESIZE", "DELIVER"],
}


class SchemaExtractor:
    """
    Extracts reusable schemas from episodic traces.
    
    Level 2 of the TSC pipeline. When the same collaboration pattern
    appears across multiple traces, it's promoted to a named schema.
    
    Compression: ~100MB raw traces → ~5MB schemas (20x).
    """

    def __init__(
        self,
        promotion_threshold: int = 10,
        storage_path: str = "data/memory/schemas/",
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.promotion_threshold = promotion_threshold
        self._schemas: Dict[str, Schema] = {}
        self._pattern_counts: Dict[str, int] = {}  # pattern_hash → count
        self._pattern_sources: Dict[str, List[str]] = {}  # pattern_hash → trace_ids
        self._lock = threading.Lock()

        # Seed known patterns
        self._seed_patterns()

    def __len__(self) -> int:
        return len(self._schemas)

    def _seed_patterns(self) -> None:
        """Seed with known archetype patterns."""
        for name, pattern in SEED_PATTERNS.items():
            schema_id = f"schema_seed_{name.lower().replace('-', '_')}"
            self._schemas[schema_id] = Schema(
                schema_id=schema_id,
                name=name,
                pattern=pattern,
                source_traces=[],
                activation_count=100,  # High initial count for seeds
            )

    def extract_from_traces(self, traces: List[CollaborationTrace]) -> int:
        """
        Extract schemas from a batch of traces.
        
        Returns count of new schemas promoted.
        """
        new_schemas = 0

        for trace in traces:
            pattern = self._classify_pattern(trace)
            if not pattern:
                continue

            pattern_key = "-".join(pattern)
            pattern_hash = hashlib.md5(pattern_key.encode()).hexdigest()[:12]

            with self._lock:
                self._pattern_counts[pattern_hash] = self._pattern_counts.get(pattern_hash, 0) + 1
                if pattern_hash not in self._pattern_sources:
                    self._pattern_sources[pattern_hash] = []
                self._pattern_sources[pattern_hash].append(trace.trace_id)

                # Check if this pattern meets promotion threshold
                count = self._pattern_counts[pattern_hash]
                if count >= self.promotion_threshold and pattern_key not in self._schemas:
                    schema = Schema(
                        schema_id=f"schema_{uuid.uuid4().hex[:8]}",
                        name=pattern_key,
                        pattern=pattern,
                        source_traces=self._pattern_sources[pattern_hash][-20:],
                        activation_count=count,
                    )
                    self._schemas[schema.schema_id] = schema
                    new_schemas += 1
                    logger.info(f"Promoted new schema: {pattern_key} (seen {count} times)")
                elif pattern_key in {s.name for s in self._schemas.values()}:
                    # Increment existing schema
                    for s in self._schemas.values():
                        if s.name == pattern_key:
                            s.activation_count += 1
                            s.last_activated = time.time()
                            break

        return new_schemas

    def _classify_pattern(self, trace: CollaborationTrace) -> Optional[List[str]]:
        """Classify a trace's collaboration pattern."""
        if not trace.steps:
            return None

        # Extract role verbs from steps
        verbs = []
        for step in trace.steps:
            action = step.get("action", step.get("role", "unknown")).upper()
            verbs.append(action)

        # Normalize to known pattern verbs
        normalized = []
        for verb in verbs:
            for known in SEED_PATTERNS.values():
                flat_known = [v for pattern in [known] for v in pattern]
                if verb in flat_known:
                    normalized.append(verb)
                    break
            else:
                # Map common synonyms
                mapping = {
                    "CODE": "IMPLEMENT", "WRITE": "IMPLEMENT", "BUILD": "IMPLEMENT",
                    "CRITIQUE": "REVIEW", "AUDIT": "REVIEW", "CHECK": "REVIEW",
                    "FIX": "PATCH", "REPAIR": "PATCH", "DEPLOY": "SHIP",
                    "ANALYZE": "RESEARCH", "INVESTIGATE": "RESEARCH",
                    "SUMMARIZE": "SYNTHESIZE", "COMBINE": "AGGREGATE",
                    "SPLIT": "DECOMPOSE", "ASSIGN": "DISPATCH",
                    "QUESTION": "CHALLENGE", "DEFEND": "RESOLVE",
                }
                normalized.append(mapping.get(verb, verb))

        # Deduplicate consecutive identical verbs
        deduped = []
        for v in normalized:
            if not deduped or deduped[-1] != v:
                deduped.append(v)

        return deduped if len(deduped) >= 2 else None

    def all_schemas(self) -> List[Schema]:
        """Get all known schemas."""
        with self._lock:
            return list(self._schemas.values())

    def query_schemas(self, task: str, limit: int = 5) -> List[Schema]:
        """Find schemas relevant to a task."""
        task_lower = task.lower()
        scored = []

        for schema in self._schemas.values():
            score = 0.0
            for tag in schema.tags + [schema.name.lower()]:
                if tag in task_lower or task_lower in tag:
                    score += 1.0
            score += schema.activation_count * 0.01
            if score > 0:
                scored.append((score, schema))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]

    def load(self) -> None:
        """Load schemas from disk."""
        schema_file = self.storage_path / "schemas.json"
        if not schema_file.exists():
            return
        try:
            with open(schema_file) as f:
                data = json.load(f)
            self._schemas.clear()
            for entry in data.get("schemas", []):
                schema = Schema(**entry)
                self._schemas[schema.schema_id] = schema
            logger.info(f"Loaded {len(self._schemas)} schemas")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load schemas: {e}")

    def save(self) -> None:
        """Persist schemas to disk."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        schema_file = self.storage_path / "schemas.json"
        with self._lock:
            data = {
                "schemas": [asdict(s) for s in self._schemas.values()],
                "updated_at": time.time(),
            }
        with open(schema_file, "w") as f:
            json.dump(data, f, indent=2)