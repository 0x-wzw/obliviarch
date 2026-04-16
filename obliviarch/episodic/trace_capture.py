"""
Trace Capture — Episodic trace recording (Level 1 of TSC).

Records raw multi-agent collaboration traces:
- Who participated
- What steps were taken
- What the outcome was
- Time-to-live before archival

These traces are the raw material for schema extraction.
High fidelity, high cost. Kept for <24h (hot) to <48h (warm).
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading

logger = __import__("logging").getLogger(__name__)


@dataclass
class CollaborationTrace:
    """A recorded multi-agent collaboration trace."""
    trace_id: str
    agents: List[str]
    task: str
    steps: List[Dict[str, Any]]
    outcome: str
    score: float
    created_at: float
    archived: bool = False

    def __post_init__(self):
        pass


class TraceCapture:
    """
    Records episodic traces of multi-agent collaboration.
    
    Level 1 of the Trace Schema Compression pipeline.
    Raw interaction logs — high fidelity, high storage cost.
    Consolidated into schemas after 24h.
    """

    def __init__(self, storage_path: str = "data/memory/episodic/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._traces: Dict[str, CollaborationTrace] = {}
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self._traces)

    def record(
        self,
        agents: List[str],
        task: str,
        steps: List[Dict[str, Any]],
        outcome: str,
        score: float,
    ) -> str:
        """Record a collaboration trace."""
        trace_id = f"trace_{uuid.uuid4().hex[:10]}"
        trace = CollaborationTrace(
            trace_id=trace_id,
            agents=agents,
            task=task,
            steps=steps,
            outcome=outcome,
            score=score,
            created_at=time.time(),
        )

        with self._lock:
            self._traces[trace_id] = trace

        logger.debug(f"Captured trace {trace_id} with {len(agents)} agents")
        return trace_id

    def recent_traces(self, hours: float = 24.0) -> List[CollaborationTrace]:
        """Get traces from the last N hours."""
        cutoff = time.time() - (hours * 3600)
        with self._lock:
            return [
                t for t in self._traces.values()
                if t.created_at >= cutoff and not t.archived
            ]

    def archive_older_than(self, hours: float = 48.0) -> int:
        """Mark traces older than N hours as archived."""
        cutoff = time.time() - (hours * 3600)
        archived = 0

        with self._lock:
            for trace in self._traces.values():
                if trace.created_at < cutoff and not trace.archived:
                    trace.archived = True
                    archived += 1

        if archived:
            logger.info(f"Archived {archived} traces older than {hours}h")
        return archived

    def get_unarchived(self) -> List[CollaborationTrace]:
        """Get all non-archived traces."""
        with self._lock:
            return [t for t in self._traces.values() if not t.archived]

    def load(self) -> None:
        """Load traces from disk."""
        trace_file = self.storage_path / "traces.json"
        if not trace_file.exists():
            return
        try:
            with open(trace_file) as f:
                data = json.load(f)
            for entry in data.get("traces", []):
                trace = CollaborationTrace(**entry)
                self._traces[trace.trace_id] = trace
            logger.info(f"Loaded {len(self._traces)} traces")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load traces: {e}")

    def save(self) -> None:
        """Persist traces to disk."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        trace_file = self.storage_path / "traces.json"
        with self._lock:
            data = {
                "traces": [asdict(t) for t in self._traces.values()],
                "updated_at": time.time(),
            }
        with open(trace_file, "w") as f:
            json.dump(data, f, indent=2)